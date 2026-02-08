"""
Nachos Replay for Guaca - Audit Service
Handles audit logging for all system operations.
"""
import logging
import csv
import json
from io import StringIO
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, AuditAction, User, Replay
from app.schemas import AuditLogSearch, PaginationParams

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log(
        self,
        action: AuditAction,
        user_id: Optional[UUID] = None,
        username: Optional[str] = None,
        replay_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Create an audit log entry.
        This operation is designed to never fail silently.
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                username=username,
                replay_id=replay_id,
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details or {}
            )
            
            self.db.add(audit_log)
            await self.db.flush()
            
            logger.info(
                f"Audit: {action.value} by {username or 'anonymous'} "
                f"from {ip_address or 'unknown'}"
            )
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Re-raise to ensure audit failures are noticed
            raise
    
    async def get_logs(
        self,
        filters: Optional[AuditLogSearch] = None,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[AuditLog], int]:
        """Get audit logs with filtering and pagination."""
        query = select(AuditLog)
        count_query = select(func.count(AuditLog.id))
        
        # Apply filters
        if filters:
            conditions = []
            
            if filters.user_id:
                conditions.append(AuditLog.user_id == filters.user_id)
            
            if filters.username:
                conditions.append(AuditLog.username.ilike(f"%{filters.username}%"))
            
            if filters.replay_id:
                conditions.append(AuditLog.replay_id == filters.replay_id)
            
            if filters.action:
                conditions.append(AuditLog.action == filters.action)
            
            if filters.ip_address:
                conditions.append(AuditLog.ip_address.ilike(f"%{filters.ip_address}%"))
            
            if filters.date_from:
                conditions.append(AuditLog.created_at >= filters.date_from)
            
            if filters.date_to:
                conditions.append(AuditLog.created_at <= filters.date_to)
            
            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        if pagination:
            # Sorting
            sort_column = getattr(AuditLog, pagination.sort_by or "created_at", AuditLog.created_at)
            if pagination.sort_order == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
            
            # Offset and limit
            offset = (pagination.page - 1) * pagination.page_size
            query = query.offset(offset).limit(pagination.page_size)
        else:
            # Para exportação sem paginação, usar limite alto
            query = query.order_by(AuditLog.created_at.desc()).limit(10000)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return list(logs), total
    
    async def export_csv(
        self,
        filters: Optional[AuditLogSearch] = None
    ) -> str:
        """Export audit logs to CSV format."""
        # Buscar todos os logs sem limite de paginação (usar None)
        logs, _ = await self.get_logs(
            filters=filters,
            pagination=None  # Sem limite para exportação
        )
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "ID",
            "Timestamp",
            "User ID",
            "Username",
            "Action",
            "Replay ID",
            "IP Address",
            "User Agent",
            "Details"
        ])
        
        # Data
        for log in logs:
            writer.writerow([
                str(log.id),
                log.created_at.isoformat(),
                str(log.user_id) if log.user_id else "",
                log.username or "",
                log.action.value,
                str(log.replay_id) if log.replay_id else "",
                log.ip_address or "",
                log.user_agent or "",
                json.dumps(log.details)
            ])
        
        return output.getvalue()
    
    async def export_json(
        self,
        filters: Optional[AuditLogSearch] = None
    ) -> str:
        """Export audit logs to JSON format."""
        # Buscar todos os logs sem limite de paginação (usar None)
        logs, _ = await self.get_logs(
            filters=filters,
            pagination=None  # Sem limite para exportação
        )
        
        data = []
        for log in logs:
            data.append({
                "id": str(log.id),
                "timestamp": log.created_at.isoformat(),
                "user_id": str(log.user_id) if log.user_id else None,
                "username": log.username,
                "action": log.action.value,
                "replay_id": str(log.replay_id) if log.replay_id else None,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "details": log.details
            })
        
        return json.dumps(data, indent=2)
    
    async def get_stats(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get audit statistics."""
        conditions = []
        
        if date_from:
            conditions.append(AuditLog.created_at >= date_from)
        if date_to:
            conditions.append(AuditLog.created_at <= date_to)
        
        # Total logs
        total_query = select(func.count(AuditLog.id))
        if conditions:
            total_query = total_query.where(and_(*conditions))
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0
        
        # Logs by action
        action_query = (
            select(AuditLog.action, func.count(AuditLog.id))
            .group_by(AuditLog.action)
        )
        if conditions:
            action_query = action_query.where(and_(*conditions))
        action_result = await self.db.execute(action_query)
        by_action = {row[0].value: row[1] for row in action_result.fetchall()}
        
        # Top users
        user_query = (
            select(AuditLog.username, func.count(AuditLog.id))
            .where(AuditLog.username.isnot(None))
            .group_by(AuditLog.username)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
        )
        if conditions:
            user_query = user_query.where(and_(*conditions))
        user_result = await self.db.execute(user_query)
        top_users = [
            {"username": row[0], "count": row[1]}
            for row in user_result.fetchall()
        ]
        
        return {
            "total": total,
            "by_action": by_action,
            "top_users": top_users
        }
