"""
Nachos Replay for Guaca - API Dependencies
Common dependencies for API endpoints.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, UserRole, TokenBlacklist, Group
from app.utils.security import decode_token
from app.services.audit_service import AuditService
from app.services.replay_service import ReplayService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise credentials_exception
    
    # Check token type
    if payload.get("type") != "access":
        raise credentials_exception
    
    # Check if token is blacklisted
    jti = payload.get("jti")
    if jti:
        blacklisted = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.token_jti == jti)
        )
        if blacklisted.scalar_one_or_none():
            raise credentials_exception
    
    # Get user
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception
    
    result = await db.execute(
        select(User)
        .options(selectinload(User.groups))
        .where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    return current_user


def require_role(*roles: UserRole):
    """Dependency factory to require specific roles."""
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(r.value for r in roles)}"
            )
        return current_user
    return role_checker


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_auditor_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require auditor or admin role."""
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auditor access required"
        )
    return current_user


async def get_audit_service(
    db: AsyncSession = Depends(get_db)
) -> AuditService:
    """Get audit service instance."""
    return AuditService(db)


async def get_replay_service(
    db: AsyncSession = Depends(get_db)
) -> ReplayService:
    """Get replay service instance."""
    return ReplayService(db)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    # Check for forwarded IP (when behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    if request.client:
        return request.client.host
    
    return "unknown"


async def get_allowed_usernames(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Optional[List[str]]:
    """
    Get list of usernames the current user can view replays for.
    Returns None for admins (can see all).
    Returns list of subordinate usernames for others.
    """
    # Admins can see everything
    if current_user.role == UserRole.ADMIN:
        return None
    
    # Auditors can see everything
    if current_user.role == UserRole.AUDITOR:
        return None
    
    allowed = [current_user.username]
    
    # Get subordinate users from group hierarchy
    if current_user.groups:
        group_ids = [g.id for g in current_user.groups]
        
        # Find all child groups recursively
        child_group_ids = set()
        to_process = list(group_ids)
        
        while to_process:
            current_id = to_process.pop()
            
            result = await db.execute(
                select(Group)
                .options(selectinload(Group.child_groups))
                .where(Group.id == current_id)
            )
            group = result.scalar_one_or_none()
            
            if group and group.child_groups:
                for child in group.child_groups:
                    if child.id not in child_group_ids:
                        child_group_ids.add(child.id)
                        to_process.append(child.id)
        
        # Get users from child groups
        if child_group_ids:
            from app.models import UserGroup
            
            user_result = await db.execute(
                select(User.username)
                .join(UserGroup)
                .where(UserGroup.group_id.in_(child_group_ids))
            )
            for row in user_result.fetchall():
                if row[0] not in allowed:
                    allowed.append(row[0])
    
    return allowed
