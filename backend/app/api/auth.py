"""
Nachos Replay for Guaca - Authentication API
Login, logout, token refresh endpoints.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserRole, TokenBlacklist, AuditAction
from app.schemas import (
    LoginRequest, TokenResponse, TokenRefreshRequest, CurrentUser
)
from app.utils.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token,
    decode_token, get_token_jti, get_token_expiry
)
from app.services.ldap_service import get_ldap_service
from app.services.audit_service import AuditService
from app.api.deps import get_current_user, get_client_ip, get_audit_service
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    Supports both LDAP and local authentication.
    """
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    audit_service = AuditService(db)
    
    user = None
    ldap_user = None
    
    # Try LDAP authentication first
    ldap_service = get_ldap_service()
    ldap_user = ldap_service.authenticate(login_data.username, login_data.password)
    
    if ldap_user:
        # Find or create user from LDAP
        result = await db.execute(
            select(User).where(User.username == ldap_user.username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user from LDAP
            user = User(
                username=ldap_user.username,
                email=ldap_user.email,
                display_name=ldap_user.display_name,
                ldap_dn=ldap_user.dn,
                is_ldap_user=True,
                role=UserRole.VIEWER,  # Default role
                is_active=True
            )
            db.add(user)
            await db.flush()
        else:
            # Update user info from LDAP
            user.email = ldap_user.email or user.email
            user.display_name = ldap_user.display_name or user.display_name
            user.ldap_dn = ldap_user.dn
    else:
        # Try local authentication
        result = await db.execute(
            select(User).where(User.username == login_data.username)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.password_hash:
            await audit_service.log(
                action=AuditAction.LOGIN,
                username=login_data.username,
                ip_address=client_ip,
                user_agent=user_agent,
                details={"success": False, "reason": "Invalid credentials"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        if not verify_password(login_data.password, user.password_hash):
            await audit_service.log(
                action=AuditAction.LOGIN,
                user_id=user.id,
                username=user.username,
                ip_address=client_ip,
                user_agent=user_agent,
                details={"success": False, "reason": "Invalid password"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
    
    if not user.is_active:
        await audit_service.log(
            action=AuditAction.LOGIN,
            user_id=user.id,
            username=user.username,
            ip_address=client_ip,
            user_agent=user_agent,
            details={"success": False, "reason": "Account disabled"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    
    # Create tokens
    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Log successful login
    await audit_service.log(
        action=AuditAction.LOGIN,
        user_id=user.id,
        username=user.username,
        ip_address=client_ip,
        user_agent=user_agent,
        details={"success": True, "ldap": ldap_user is not None}
    )
    
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token."""
    payload = decode_token(data.refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Check if token is blacklisted
    jti = payload.get("jti")
    if jti:
        blacklisted = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.token_jti == jti)
        )
        if blacklisted.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    # Blacklist old refresh token
    if jti:
        expires_at = get_token_expiry(data.refresh_token)
        if expires_at:
            blacklist_entry = TokenBlacklist(
                token_jti=jti,
                expires_at=expires_at
            )
            db.add(blacklist_entry)
            await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logout and invalidate current token."""
    # Get token from header
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    
    jti = get_token_jti(token)
    expires_at = get_token_expiry(token)
    
    if jti and expires_at:
        blacklist_entry = TokenBlacklist(
            token_jti=jti,
            expires_at=expires_at
        )
        db.add(blacklist_entry)
    
    # Log logout
    audit_service = AuditService(db)
    await audit_service.log(
        action=AuditAction.LOGOUT,
        user_id=current_user.id,
        username=current_user.username,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent", "")
    )
    
    await db.commit()
    
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=CurrentUser)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return CurrentUser(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role,
        groups=[g.name for g in current_user.groups]
    )
