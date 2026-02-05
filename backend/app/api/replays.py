"""
Nachos Replay for Guaca - Replays API
Endpoints for replay management and streaming.
"""
from typing import Optional
from uuid import UUID
import math

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, AuditAction
from app.schemas import (
    ReplayResponse, ReplayDetail, ReplaySearch, ReplayUpdate,
    PaginationParams, PaginatedResponse
)
from app.services.replay_service import ReplayService
from app.services.audit_service import AuditService
from app.api.deps import (
    get_current_active_user, get_admin_user,
    get_replay_service, get_audit_service,
    get_client_ip, get_allowed_usernames
)

router = APIRouter(prefix="/replays", tags=["Replays"])


@router.get("", response_model=PaginatedResponse)
async def list_replays(
    request: Request,
    query: Optional[str] = Query(None, description="Search query"),
    username: Optional[str] = Query(None, description="Filter by username"),
    session_name: Optional[str] = Query(None, description="Filter by session name"),
    client_ip: Optional[str] = Query(None, description="Filter by client IP"),
    date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_active_user),
    allowed_usernames: Optional[list] = Depends(get_allowed_usernames),
    replay_service: ReplayService = Depends(get_replay_service),
    audit_service: AuditService = Depends(get_audit_service)
):
    """List replays with filtering and pagination."""
    from datetime import datetime
    
    # Build filters
    filters = ReplaySearch(
        query=query,
        username=username,
        session_name=session_name,
        client_ip=client_ip
    )
    
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
    
    if status:
        from app.models import ReplayStatus
        try:
            filters.status = ReplayStatus(status)
        except ValueError:
            pass
    
    pagination = PaginationParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    replays, total = await replay_service.search_replays(
        filters=filters,
        pagination=pagination,
        user_id=current_user.id,
        allowed_usernames=allowed_usernames
    )
    
    # Log search action
    await audit_service.log(
        action=AuditAction.SEARCH,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent", ""),
        details={"query": query, "results_count": len(replays)}
    )
    
    return PaginatedResponse(
        items=[ReplayResponse.model_validate(r) for r in replays],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1
    )


@router.get("/{replay_id}", response_model=ReplayDetail)
async def get_replay(
    replay_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    allowed_usernames: Optional[list] = Depends(get_allowed_usernames),
    replay_service: ReplayService = Depends(get_replay_service),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Get replay details by ID."""
    replay = await replay_service.get_replay(replay_id)
    
    if not replay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay not found"
        )
    
    # Check access
    if allowed_usernames is not None:
        if replay.owner_username not in allowed_usernames and replay.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this replay"
            )
    
    # Log view action
    await audit_service.log(
        action=AuditAction.VIEW,
        user_id=current_user.id,
        username=current_user.username,
        replay_id=replay.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent", ""),
        details={"filename": replay.filename}
    )
    
    return ReplayDetail.model_validate(replay)


@router.get("/{replay_id}/stream")
async def stream_replay(
    replay_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    allowed_usernames: Optional[list] = Depends(get_allowed_usernames),
    replay_service: ReplayService = Depends(get_replay_service),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Stream replay file content."""
    replay = await replay_service.get_replay(replay_id)
    
    if not replay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay not found"
        )
    
    # Check access
    if allowed_usernames is not None:
        if replay.owner_username not in allowed_usernames and replay.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this replay"
            )
    
    file_handle = await replay_service.get_replay_file(replay)
    
    if not file_handle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay file not found"
        )
    
    # Log download action
    await audit_service.log(
        action=AuditAction.DOWNLOAD,
        user_id=current_user.id,
        username=current_user.username,
        replay_id=replay.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent", ""),
        details={"filename": replay.filename}
    )
    
    def iterfile():
        try:
            while chunk := file_handle.read(65536):
                yield chunk
        finally:
            file_handle.close()
    
    return StreamingResponse(
        iterfile(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{replay.filename}"',
            "Content-Length": str(replay.file_size)
        }
    )


@router.patch("/{replay_id}", response_model=ReplayDetail)
async def update_replay(
    replay_id: UUID,
    update_data: ReplayUpdate,
    current_user: User = Depends(get_admin_user),
    replay_service: ReplayService = Depends(get_replay_service),
    db: AsyncSession = Depends(get_db)
):
    """Update replay metadata (admin only)."""
    replay = await replay_service.get_replay(replay_id)
    
    if not replay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay not found"
        )
    
    if update_data.session_name is not None:
        replay.session_name = update_data.session_name
    
    if update_data.status is not None:
        from app.models import ReplayStatus
        replay.status = ReplayStatus(update_data.status)
    
    await db.commit()
    await db.refresh(replay)
    
    return ReplayDetail.model_validate(replay)


@router.delete("/{replay_id}")
async def delete_replay(
    replay_id: UUID,
    hard_delete: bool = Query(False, description="Permanently delete file"),
    current_user: User = Depends(get_admin_user),
    replay_service: ReplayService = Depends(get_replay_service)
):
    """Delete or archive a replay (admin only)."""
    replay = await replay_service.get_replay(replay_id)
    
    if not replay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay not found"
        )
    
    success = await replay_service.delete_replay(replay, hard_delete=hard_delete)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete replay"
        )
    
    return {"message": "Replay deleted successfully"}
