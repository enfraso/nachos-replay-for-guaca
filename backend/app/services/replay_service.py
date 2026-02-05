"""
Nachos Replay for Guaca - Replay Service
Handles replay file management, monitoring, and storage.
"""
import os
import shutil
import gzip
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, BinaryIO
from uuid import UUID
import json
import re

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Replay, ReplayStatus, User
from app.schemas import ReplaySearch, ReplayCreate, PaginationParams

logger = logging.getLogger(__name__)


class ReplayService:
    """Service for replay file operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.source_path = Path(settings.guacamole_recordings_path)
        self.storage_path = Path(settings.replay_storage_path)
    
    async def scan_for_new_replays(self) -> List[str]:
        """
        Scan the Guacamole recordings directory for new replay files.
        Only imports files older than the configured delay.
        """
        if not self.source_path.exists():
            logger.warning(f"Guacamole recordings path does not exist: {self.source_path}")
            return []
        
        imported = []
        delay_hours = settings.replay_import_delay_hours
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=delay_hours)
        
        for file_path in self.source_path.rglob("*.guac"):
            try:
                # Check file modification time
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
                
                if mtime > cutoff_time:
                    logger.debug(f"Skipping recent file: {file_path}")
                    continue
                
                # Check if already imported
                existing = await self.db.execute(
                    select(Replay).where(Replay.filename == file_path.name)
                )
                if existing.scalar_one_or_none():
                    continue
                
                # Import the replay
                replay = await self.import_replay(file_path)
                if replay:
                    imported.append(replay.filename)
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        return imported
    
    async def import_replay(self, source_file: Path) -> Optional[Replay]:
        """Import a single replay file into the system."""
        try:
            # Parse filename for metadata
            # Guacamole format: username_sessionid_timestamp.guac
            metadata = self._parse_replay_filename(source_file.name)
            
            # Create storage directory structure: YYYY/MM/
            now = datetime.now(timezone.utc)
            target_dir = self.storage_path / str(now.year) / f"{now.month:02d}"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy file to storage
            target_file = target_dir / source_file.name
            shutil.copy2(source_file, target_file)
            
            # Get file info
            file_stats = target_file.stat()
            
            # Try to extract duration from replay file
            duration = await self._extract_replay_duration(target_file)
            
            # Create database record
            replay = Replay(
                filename=source_file.name,
                original_path=str(source_file),
                stored_path=str(target_file),
                session_name=metadata.get("session_name"),
                owner_username=metadata.get("username"),
                client_ip=metadata.get("client_ip"),
                file_size=file_stats.st_size,
                duration_seconds=duration,
                session_start=metadata.get("timestamp"),
                session_end=metadata.get("timestamp") + timedelta(seconds=duration) if metadata.get("timestamp") and duration else None,
                status=ReplayStatus.ACTIVE,
                metadata_json=metadata
            )
            
            # Try to link to existing user
            if metadata.get("username"):
                user_result = await self.db.execute(
                    select(User).where(User.username == metadata["username"])
                )
                user = user_result.scalar_one_or_none()
                if user:
                    replay.owner_id = user.id
            
            self.db.add(replay)
            await self.db.flush()
            
            logger.info(f"Imported replay: {source_file.name}")
            return replay
            
        except Exception as e:
            logger.error(f"Failed to import replay {source_file}: {e}")
            return None
    
    def _parse_replay_filename(self, filename: str) -> Dict[str, Any]:
        """Parse Guacamole replay filename for metadata."""
        metadata = {
            "original_filename": filename,
            "session_name": filename.replace(".guac", "")
        }
        
        # Try to parse common formats
        # Format 1: username_connection_timestamp.guac
        # Format 2: connection-id_timestamp.guac
        
        name_without_ext = filename.replace(".guac", "")
        parts = name_without_ext.split("_")
        
        if len(parts) >= 2:
            metadata["username"] = parts[0]
            
            # Try to parse timestamp from last part
            try:
                timestamp_str = parts[-1]
                if len(timestamp_str) == 13:  # Milliseconds
                    metadata["timestamp"] = datetime.fromtimestamp(
                        int(timestamp_str) / 1000, tz=timezone.utc
                    )
                elif len(timestamp_str) == 10:  # Seconds
                    metadata["timestamp"] = datetime.fromtimestamp(
                        int(timestamp_str), tz=timezone.utc
                    )
            except (ValueError, OSError):
                pass
        
        return metadata
    
    async def _extract_replay_duration(self, file_path: Path) -> int:
        """
        Extract duration from Guacamole replay file.
        The format is: timestamp.instruction;
        We find the last timestamp to get duration.
        """
        try:
            duration = 0
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read in chunks from the end
                f.seek(0, 2)
                file_size = f.tell()
                
                # Read last 10KB
                read_size = min(10240, file_size)
                f.seek(max(0, file_size - read_size))
                content = f.read()
                
                # Find timestamps (format: timestamp.instruction)
                timestamps = re.findall(r'^(\d+)\.\w+', content, re.MULTILINE)
                
                if timestamps:
                    duration = int(timestamps[-1]) // 1000  # Convert ms to seconds
            
            return duration
            
        except Exception as e:
            logger.debug(f"Could not extract duration from {file_path}: {e}")
            return 0
    
    async def get_replay(self, replay_id: UUID) -> Optional[Replay]:
        """Get a single replay by ID."""
        result = await self.db.execute(
            select(Replay).where(Replay.id == replay_id)
        )
        return result.scalar_one_or_none()
    
    async def get_replay_by_filename(self, filename: str) -> Optional[Replay]:
        """Get a replay by filename."""
        result = await self.db.execute(
            select(Replay).where(Replay.filename == filename)
        )
        return result.scalar_one_or_none()
    
    async def search_replays(
        self,
        filters: Optional[ReplaySearch] = None,
        pagination: Optional[PaginationParams] = None,
        user_id: Optional[UUID] = None,
        allowed_usernames: Optional[List[str]] = None
    ) -> tuple[List[Replay], int]:
        """Search replays with filtering and pagination."""
        query = select(Replay)
        count_query = select(func.count(Replay.id))
        
        conditions = []
        
        # Apply access control
        if allowed_usernames is not None:
            if allowed_usernames:
                conditions.append(
                    or_(
                        Replay.owner_username.in_(allowed_usernames),
                        Replay.owner_id == user_id
                    )
                )
            elif user_id:
                conditions.append(Replay.owner_id == user_id)
        
        # Apply filters
        if filters:
            if filters.query:
                search_term = f"%{filters.query}%"
                conditions.append(
                    or_(
                        Replay.filename.ilike(search_term),
                        Replay.session_name.ilike(search_term),
                        Replay.owner_username.ilike(search_term)
                    )
                )
            
            if filters.username:
                conditions.append(Replay.owner_username.ilike(f"%{filters.username}%"))
            
            if filters.session_name:
                conditions.append(Replay.session_name.ilike(f"%{filters.session_name}%"))
            
            if filters.client_ip:
                conditions.append(Replay.client_ip.ilike(f"%{filters.client_ip}%"))
            
            if filters.date_from:
                conditions.append(Replay.session_start >= filters.date_from)
            
            if filters.date_to:
                conditions.append(Replay.session_start <= filters.date_to)
            
            if filters.status:
                conditions.append(Replay.status == filters.status)
            
            if filters.min_duration:
                conditions.append(Replay.duration_seconds >= filters.min_duration)
            
            if filters.max_duration:
                conditions.append(Replay.duration_seconds <= filters.max_duration)
        
        # Default: only active replays
        if not filters or not filters.status:
            conditions.append(Replay.status == ReplayStatus.ACTIVE)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        if pagination:
            sort_column = getattr(
                Replay,
                pagination.sort_by or "imported_at",
                Replay.imported_at
            )
            if pagination.sort_order == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
            
            offset = (pagination.page - 1) * pagination.page_size
            query = query.offset(offset).limit(pagination.page_size)
        else:
            query = query.order_by(Replay.imported_at.desc()).limit(50)
        
        result = await self.db.execute(query)
        replays = result.scalars().all()
        
        return list(replays), total
    
    async def get_replay_file(self, replay: Replay) -> Optional[BinaryIO]:
        """Get replay file for streaming."""
        if not replay.stored_path:
            return None
        
        file_path = Path(replay.stored_path)
        
        if not file_path.exists():
            logger.error(f"Replay file not found: {file_path}")
            return None
        
        return open(file_path, 'rb')
    
    async def delete_replay(self, replay: Replay, hard_delete: bool = False) -> bool:
        """Delete or archive a replay."""
        try:
            if hard_delete:
                # Remove file
                if replay.stored_path:
                    file_path = Path(replay.stored_path)
                    if file_path.exists():
                        file_path.unlink()
                
                # Remove database record
                await self.db.delete(replay)
            else:
                # Soft delete (archive)
                replay.status = ReplayStatus.DELETED
            
            await self.db.flush()
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete replay {replay.id}: {e}")
            return False
    
    async def archive_old_replays(self) -> int:
        """Archive replays older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.retention_days)
        
        result = await self.db.execute(
            select(Replay).where(
                and_(
                    Replay.status == ReplayStatus.ACTIVE,
                    Replay.imported_at < cutoff
                )
            )
        )
        replays = result.scalars().all()
        
        archived_count = 0
        
        for replay in replays:
            try:
                # Compress file if enabled
                if settings.archive_enabled and replay.stored_path:
                    await self._compress_replay(replay)
                
                replay.status = ReplayStatus.ARCHIVED
                archived_count += 1
                
            except Exception as e:
                logger.error(f"Failed to archive replay {replay.id}: {e}")
        
        await self.db.flush()
        logger.info(f"Archived {archived_count} old replays")
        
        return archived_count
    
    async def _compress_replay(self, replay: Replay):
        """Compress a replay file with gzip."""
        if not replay.stored_path:
            return
        
        source = Path(replay.stored_path)
        if not source.exists():
            return
        
        target = source.with_suffix('.guac.gz')
        
        with open(source, 'rb') as f_in:
            with gzip.open(target, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Update stored path and remove original
        replay.stored_path = str(target)
        source.unlink()
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        # Total and by status
        status_query = (
            select(Replay.status, func.count(Replay.id), func.sum(Replay.file_size))
            .group_by(Replay.status)
        )
        status_result = await self.db.execute(status_query)
        
        by_status = {}
        total_size = 0
        total_count = 0
        
        for status, count, size in status_result.fetchall():
            by_status[status.value] = {
                "count": count,
                "size_bytes": size or 0
            }
            total_count += count
            total_size += size or 0
        
        # Disk usage
        disk_total = 0
        disk_used = 0
        disk_free = 0
        
        try:
            if self.storage_path.exists():
                stat = shutil.disk_usage(self.storage_path)
                disk_total = stat.total
                disk_used = stat.used
                disk_free = stat.free
        except Exception:
            pass
        
        return {
            "total_replays": total_count,
            "total_size_bytes": total_size,
            "by_status": by_status,
            "disk_total_bytes": disk_total,
            "disk_used_bytes": disk_used,
            "disk_free_bytes": disk_free,
            "max_storage_bytes": settings.max_storage_gb * 1024 * 1024 * 1024
        }
