"""
Nachos Replay for Guaca - Maintenance Tasks
Handles periodic maintenance operations for replay storage.
"""
import os
import gzip
import shutil
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Tuple

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Replay, ReplayStatus, StorageTier

logger = logging.getLogger(__name__)

# Constantes de política de retenção
HOT_TO_WARM_MONTHS = 4      # Mover para warm após 4 meses
WARM_TO_COLD_YEARS = 2      # Mover para cold após 2 anos
COMPRESSION_THRESHOLD = 2 * 1024 * 1024 * 1024  # 2GB em bytes


class MaintenanceService:
    """Service for replay storage maintenance operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage_path = Path(settings.replay_storage_path)
    
    async def run_tier_migration(self) -> dict:
        """
        Execute tier migration for all replays based on age.
        Returns statistics about the migration.
        """
        stats = {
            "hot_to_warm": 0,
            "warm_to_cold": 0,
            "compressed": 0,
            "errors": []
        }
        
        now = datetime.now(timezone.utc)
        hot_cutoff = now - timedelta(days=HOT_TO_WARM_MONTHS * 30)
        cold_cutoff = now - timedelta(days=WARM_TO_COLD_YEARS * 365)
        
        # Migrar HOT -> WARM (replays com mais de 4 meses)
        hot_replays = await self._get_replays_for_tier_change(
            StorageTier.HOT, 
            hot_cutoff
        )
        
        for replay in hot_replays:
            try:
                await self._migrate_to_tier(replay, StorageTier.WARM)
                stats["hot_to_warm"] += 1
            except Exception as e:
                error_msg = f"Erro ao migrar {replay.filename} para WARM: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
        
        # Migrar WARM -> COLD (replays com mais de 2 anos)
        warm_replays = await self._get_replays_for_tier_change(
            StorageTier.WARM,
            cold_cutoff
        )
        
        for replay in warm_replays:
            try:
                compressed = await self._migrate_to_tier(
                    replay, 
                    StorageTier.COLD,
                    compress_if_large=True
                )
                stats["warm_to_cold"] += 1
                if compressed:
                    stats["compressed"] += 1
            except Exception as e:
                error_msg = f"Erro ao migrar {replay.filename} para COLD: {e}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
        
        await self.db.commit()
        
        logger.info(
            f"Migração de tiers concluída: "
            f"HOT->WARM: {stats['hot_to_warm']}, "
            f"WARM->COLD: {stats['warm_to_cold']}, "
            f"Comprimidos: {stats['compressed']}"
        )
        
        return stats
    
    async def _get_replays_for_tier_change(
        self, 
        current_tier: StorageTier,
        cutoff_date: datetime
    ) -> List[Replay]:
        """Get replays that should be moved to a different tier."""
        result = await self.db.execute(
            select(Replay).where(
                and_(
                    Replay.storage_tier == current_tier,
                    Replay.status == ReplayStatus.ACTIVE,
                    Replay.imported_at <= cutoff_date
                )
            )
        )
        return list(result.scalars().all())
    
    async def _migrate_to_tier(
        self, 
        replay: Replay, 
        new_tier: StorageTier,
        compress_if_large: bool = False
    ) -> bool:
        """
        Migrate a replay file to a new storage tier.
        Returns True if file was compressed.
        """
        if not replay.stored_path:
            return False
        
        source_path = Path(replay.stored_path)
        if not source_path.exists():
            logger.warning(f"Arquivo não encontrado: {source_path}")
            return False
        
        # Determinar novo caminho
        session_date = replay.session_start or replay.imported_at
        if new_tier == StorageTier.COLD:
            # Para COLD, apenas ano
            target_dir = self.storage_path / "cold" / str(session_date.year)
        else:
            # Para HOT e WARM, ano/mês
            target_dir = (
                self.storage_path / new_tier.value / 
                str(session_date.year) / f"{session_date.month:02d}"
            )
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Verificar se deve comprimir
        should_compress = (
            compress_if_large and 
            source_path.stat().st_size >= COMPRESSION_THRESHOLD and
            not replay.is_compressed
        )
        
        if should_compress:
            target_path = target_dir / f"{source_path.name}.gz"
            original_size = source_path.stat().st_size
            
            # Comprimir arquivo
            with open(source_path, 'rb') as f_in:
                with gzip.open(target_path, 'wb', compresslevel=6) as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remover original
            source_path.unlink()
            
            # Atualizar registro
            replay.stored_path = str(target_path)
            replay.is_compressed = True
            replay.original_size = original_size
            replay.file_size = target_path.stat().st_size
            
            logger.info(
                f"Comprimido {replay.filename}: "
                f"{original_size / 1024 / 1024:.1f}MB -> "
                f"{replay.file_size / 1024 / 1024:.1f}MB"
            )
        else:
            # Apenas mover o arquivo
            target_path = target_dir / source_path.name
            shutil.move(str(source_path), str(target_path))
            replay.stored_path = str(target_path)
        
        # Atualizar tier
        replay.storage_tier = new_tier
        
        return should_compress
    
    async def calculate_checksum(self, replay: Replay) -> str:
        """Calculate SHA-256 checksum for a replay file."""
        if not replay.stored_path:
            return ""
        
        file_path = Path(replay.stored_path)
        if not file_path.exists():
            return ""
        
        sha256_hash = hashlib.sha256()
        
        # Abrir como gzip se comprimido
        if replay.is_compressed:
            with gzip.open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
        else:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
        
        checksum = sha256_hash.hexdigest()
        replay.checksum_sha256 = checksum
        
        return checksum
    
    async def verify_integrity(self, replay: Replay) -> bool:
        """Verify replay file integrity using stored checksum."""
        if not replay.checksum_sha256:
            return True  # Sem checksum, assumir ok
        
        current_checksum = await self.calculate_checksum(replay)
        return current_checksum == replay.checksum_sha256
    
    async def get_storage_stats(self) -> dict:
        """Get statistics about storage usage by tier."""
        from sqlalchemy import func
        
        stats = {}
        
        for tier in StorageTier:
            result = await self.db.execute(
                select(
                    func.count(Replay.id),
                    func.sum(Replay.file_size)
                ).where(
                    and_(
                        Replay.storage_tier == tier,
                        Replay.status == ReplayStatus.ACTIVE
                    )
                )
            )
            row = result.first()
            stats[tier.value] = {
                "count": row[0] or 0,
                "size_bytes": row[1] or 0,
                "size_readable": self._format_size(row[1] or 0)
            }
        
        return stats
    
    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"
