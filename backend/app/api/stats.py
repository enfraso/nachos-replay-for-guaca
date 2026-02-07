"""
Nachos Replay for Guaca - Statistics API
Dashboard and statistics endpoints.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Replay, ReplayStatus, AuditLog
from app.schemas import DashboardStats, TopUser, StorageStats
from app.services.replay_service import ReplayService
from app.api.deps import get_current_active_user, get_replay_service

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("/overview", response_model=DashboardStats)
async def get_overview(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard overview statistics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    
    # Total replays
    total_result = await db.execute(
        select(func.count(Replay.id)).where(Replay.status == ReplayStatus.ACTIVE)
    )
    total_replays = total_result.scalar() or 0
    
    # Total users
    users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    total_users = users_result.scalar() or 0
    
    # Total storage
    storage_result = await db.execute(
        select(func.sum(Replay.file_size)).where(Replay.status == ReplayStatus.ACTIVE)
    )
    total_storage = storage_result.scalar() or 0
    
    # Replays today
    today_result = await db.execute(
        select(func.count(Replay.id)).where(
            and_(
                Replay.status == ReplayStatus.ACTIVE,
                Replay.imported_at >= today_start
            )
        )
    )
    replays_today = today_result.scalar() or 0
    
    # Replays this week
    week_result = await db.execute(
        select(func.count(Replay.id)).where(
            and_(
                Replay.status == ReplayStatus.ACTIVE,
                Replay.imported_at >= week_start
            )
        )
    )
    replays_this_week = week_result.scalar() or 0
    
    # Active sessions (users logged in last hour)
    hour_ago = now - timedelta(hours=1)
    active_result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.is_active == True,
                User.last_login >= hour_ago
            )
        )
    )
    active_sessions = active_result.scalar() or 0
    
    return DashboardStats(
        total_replays=total_replays,
        total_users=total_users,
        total_storage_bytes=total_storage,
        replays_today=replays_today,
        replays_this_week=replays_this_week,
        active_sessions=active_sessions
    )


@router.get("/top-users")
async def get_top_users(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get top users by replay count."""
    result = await db.execute(
        select(
            Replay.owner_username,
            func.count(Replay.id).label("count"),
            func.sum(Replay.duration_seconds).label("duration")
        )
        .where(
            and_(
                Replay.status == ReplayStatus.ACTIVE,
                Replay.owner_username.isnot(None)
            )
        )
        .group_by(Replay.owner_username)
        .order_by(func.count(Replay.id).desc())
        .limit(limit)
    )
    
    top_users = []
    for row in result.fetchall():
        # Try to get display name
        user_result = await db.execute(
            select(User.display_name).where(User.username == row[0])
        )
        display_name = user_result.scalar_one_or_none()
        
        top_users.append(TopUser(
            username=row[0],
            display_name=display_name,
            replay_count=row[1],
            total_duration_seconds=row[2] or 0
        ))
    
    return top_users


@router.get("/storage", response_model=StorageStats)
async def get_storage_stats(
    current_user: User = Depends(get_current_active_user),
    replay_service: ReplayService = Depends(get_replay_service)
):
    """Get storage statistics."""
    stats = await replay_service.get_storage_stats()
    
    return StorageStats(
        total_bytes=stats["disk_total_bytes"],
        used_bytes=stats["disk_used_bytes"],
        available_bytes=stats["disk_free_bytes"],
        replay_count_by_status=stats["by_status"]
    )


@router.get("/replays-over-time")
async def get_replays_over_time(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get replay counts over time for charts."""
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    
    # This query groups replays by date
    result = await db.execute(
        select(
            func.date_trunc('day', Replay.imported_at).label('date'),
            func.count(Replay.id).label('count'),
            func.sum(Replay.duration_seconds).label('duration')
        )
        .where(
            and_(
                Replay.status == ReplayStatus.ACTIVE,
                Replay.imported_at >= start_date
            )
        )
        .group_by(func.date_trunc('day', Replay.imported_at))
        .order_by(func.date_trunc('day', Replay.imported_at))
    )
    
    data = []
    for row in result.fetchall():
        data.append({
            "date": row[0].strftime("%Y-%m-%d"),
            "count": row[1],
            "total_duration_seconds": row[2] or 0
        })
    
    return data


@router.get("/activity-by-hour")
async def get_activity_by_hour(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get activity distribution by hour of day."""
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    
    result = await db.execute(
        select(
            func.extract('hour', AuditLog.created_at).label('hour'),
            func.count(AuditLog.id).label('count')
        )
        .where(AuditLog.created_at >= start_date)
        .group_by(func.extract('hour', AuditLog.created_at))
        .order_by(func.extract('hour', AuditLog.created_at))
    )
    
    # Initialize all hours
    hours = {i: 0 for i in range(24)}
    
    for row in result.fetchall():
        hours[int(row[0])] = row[1]
    
    return [{"hour": h, "count": c} for h, c in hours.items()]
