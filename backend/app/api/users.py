"""
Nachos Replay for Guaca - Users API
User management endpoints.
"""
from typing import Optional, List
from uuid import UUID
import math

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, UserRole, Group, UserGroup
from app.schemas import (
    UserResponse, UserCreate, UserUpdate, UserBasic,
    GroupResponse, GroupCreate, GroupUpdate, GroupBasic,
    PaginationParams, PaginatedResponse
)
from app.utils.security import hash_password
from app.api.deps import get_admin_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse)
async def list_users(
    query: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)."""
    stmt = select(User).options(selectinload(User.groups))
    count_stmt = select(func.count(User.id))
    
    if query:
        search_term = f"%{query}%"
        stmt = stmt.where(
            User.username.ilike(search_term) |
            User.display_name.ilike(search_term) |
            User.email.ilike(search_term)
        )
        count_stmt = count_stmt.where(
            User.username.ilike(search_term) |
            User.display_name.ilike(search_term) |
            User.email.ilike(search_term)
        )
    
    if role:
        try:
            role_enum = UserRole(role)
            stmt = stmt.where(User.role == role_enum)
            count_stmt = count_stmt.where(User.role == role_enum)
        except ValueError:
            pass
    
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
        count_stmt = count_stmt.where(User.is_active == is_active)
    
    # Count
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0
    
    # Pagination
    offset = (page - 1) * page_size
    stmt = stmt.order_by(User.username).offset(offset).limit(page_size)
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 1
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (admin only)."""
    # Check if username exists
    existing = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        display_name=user_data.display_name,
        role=user_data.role,
        is_active=user_data.is_active,
        password_hash=hash_password(user_data.password) if user_data.password else None
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (admin only)."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.groups))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user (admin only)."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.groups))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_data.email is not None:
        user.email = user_data.email
    
    if user_data.display_name is not None:
        user.display_name = user_data.display_name
    
    if user_data.role is not None:
        user.role = user_data.role
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    if user_data.password is not None:
        user.password_hash = hash_password(user_data.password)
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (admin only)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.delete(user)
    await db.commit()
    
    return {"message": "User deleted successfully"}


# ============================================
# Groups Management
# ============================================

groups_router = APIRouter(prefix="/groups", tags=["Groups"])


@groups_router.get("", response_model=List[GroupResponse])
async def list_groups(
    query: Optional[str] = Query(None),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all groups (admin only)."""
    stmt = select(Group).options(selectinload(Group.child_groups))
    
    if query:
        stmt = stmt.where(Group.name.ilike(f"%{query}%"))
    
    result = await db.execute(stmt.order_by(Group.name))
    groups = result.scalars().all()
    
    # Get user counts
    responses = []
    for group in groups:
        count_result = await db.execute(
            select(func.count(UserGroup.user_id))
            .where(UserGroup.group_id == group.id)
        )
        user_count = count_result.scalar() or 0
        
        response = GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            ldap_dn=group.ldap_dn,
            created_at=group.created_at,
            user_count=user_count,
            child_groups=[GroupBasic(id=c.id, name=c.name) for c in group.child_groups]
        )
        responses.append(response)
    
    return responses


@groups_router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new group (admin only)."""
    # Check if name exists
    existing = await db.execute(
        select(Group).where(Group.name == group_data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group name already exists"
        )
    
    group = Group(
        name=group_data.name,
        description=group_data.description,
        ldap_dn=group_data.ldap_dn
    )
    
    db.add(group)
    await db.flush()
    
    # Add parent groups
    if group_data.parent_group_ids:
        from app.models import GroupHierarchy
        for parent_id in group_data.parent_group_ids:
            hierarchy = GroupHierarchy(
                parent_group_id=parent_id,
                child_group_id=group.id
            )
            db.add(hierarchy)
    
    await db.commit()
    await db.refresh(group)
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        ldap_dn=group.ldap_dn,
        created_at=group.created_at,
        user_count=0,
        child_groups=[]
    )


@groups_router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: UUID,
    group_data: GroupUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update group (admin only)."""
    result = await db.execute(
        select(Group)
        .options(selectinload(Group.child_groups))
        .where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    if group_data.name is not None:
        group.name = group_data.name
    
    if group_data.description is not None:
        group.description = group_data.description
    
    await db.commit()
    await db.refresh(group)
    
    count_result = await db.execute(
        select(func.count(UserGroup.user_id))
        .where(UserGroup.group_id == group.id)
    )
    user_count = count_result.scalar() or 0
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        ldap_dn=group.ldap_dn,
        created_at=group.created_at,
        user_count=user_count,
        child_groups=[GroupBasic(id=c.id, name=c.name) for c in group.child_groups]
    )


@groups_router.delete("/{group_id}")
async def delete_group(
    group_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete group (admin only)."""
    result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    await db.delete(group)
    await db.commit()
    
    return {"message": "Group deleted successfully"}


@groups_router.post("/{group_id}/users/{user_id}")
async def add_user_to_group(
    group_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Add user to group (admin only)."""
    # Verify group exists
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    if not group_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already member
    existing = await db.execute(
        select(UserGroup).where(
            UserGroup.user_id == user_id,
            UserGroup.group_id == group_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already in group")
    
    user_group = UserGroup(user_id=user_id, group_id=group_id)
    db.add(user_group)
    await db.commit()
    
    return {"message": "User added to group"}


@groups_router.delete("/{group_id}/users/{user_id}")
async def remove_user_from_group(
    group_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove user from group (admin only)."""
    result = await db.execute(
        select(UserGroup).where(
            UserGroup.user_id == user_id,
            UserGroup.group_id == group_id
        )
    )
    user_group = result.scalar_one_or_none()
    
    if not user_group:
        raise HTTPException(status_code=404, detail="User not in group")
    
    await db.delete(user_group)
    await db.commit()
    
    return {"message": "User removed from group"}
