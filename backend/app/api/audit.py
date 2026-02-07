"""
Nachos Replay for Guaca - Audit API
Endpoints for audit logs and export.
"""
from typing import Optional
from uuid import UUID
import math

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, AuditAction
from app.schemas import (
    AuditLogResponse, AuditLogSearch, AuditExportRequest,
    PaginationParams, PaginatedResponse
)
from app.services.audit_service import AuditService
from app.api.deps import (
    get_auditor_user, get_audit_service, get_client_ip
)

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs", response_model=PaginatedResponse)
async def list_audit_logs(
    request: Request,
    user_id: Optional[UUID] = Query(None),
    username: Optional[str] = Query(None),
    replay_id: Optional[UUID] = Query(None),
    action: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_auditor_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """List audit logs with filtering (auditor/admin only)."""
    from datetime import datetime
    
    # Build filters
    filters = AuditLogSearch(
        user_id=user_id,
        username=username,
        replay_id=replay_id,
        ip_address=ip_address
    )
    
    if action:
        try:
            filters.action = AuditAction(action)
        except ValueError:
            pass
    
    if date_from:
        try:
            filters.date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    if date_to:
        try:
            filters.date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    logs, total = await audit_service.get_logs(
        filters=filters,
        pagination=pagination
    )
    
    return PaginatedResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1
    )


@router.get("/export")
async def export_audit_logs(
    request: Request,
    format: str = Query("csv", pattern="^(csv|json)$"),
    user_id: Optional[UUID] = Query(None),
    username: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: User = Depends(get_auditor_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Export audit logs as CSV or JSON (auditor/admin only)."""
    from datetime import datetime
    
    # Build filters
    filters = AuditLogSearch(
        user_id=user_id,
        username=username
    )
    
    if action:
        try:
            filters.action = AuditAction(action)
        except ValueError:
            pass
    
    if date_from:
        try:
            filters.date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    if date_to:
        try:
            filters.date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    # Log export action
    await audit_service.log(
        action=AuditAction.EXPORT,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent", ""),
        details={"format": format, "filters": filters.model_dump()}
    )
    
    if format == "json":
        content = await audit_service.export_json(filters)
        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=audit_logs.json"
            }
        )
    else:
        content = await audit_service.export_csv(filters)
        return Response(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=audit_logs.csv"
            }
        )


@router.get("/stats")
async def get_audit_stats(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user: User = Depends(get_auditor_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Get audit statistics (auditor/admin only)."""
    from datetime import datetime
    
    parsed_date_from = None
    parsed_date_to = None
    
    if date_from:
        try:
            parsed_date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    if date_to:
        try:
            parsed_date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    stats = await audit_service.get_stats(
        date_from=parsed_date_from,
        date_to=parsed_date_to
    )
    
    return stats
