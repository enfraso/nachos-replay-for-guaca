"""
Nachos Replay for Guaca - Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============================================
# Enums
# ============================================

class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    VIEWER = "viewer"
    AUDITOR = "auditor"


class ReplayStatusEnum(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class AuditActionEnum(str, Enum):
    VIEW = "view"
    DOWNLOAD = "download"
    SEARCH = "search"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PLAY_START = "play_start"
    PLAY_COMPLETE = "play_complete"
    UPLOAD = "upload"
    AUTH_FAILED = "auth_failed"


class StorageTierEnum(str, Enum):
    HOT = "hot"      # 0-4 meses
    WARM = "warm"    # 4 meses - 2 anos
    COLD = "cold"    # > 2 anos


# ============================================
# Authentication Schemas
# ============================================

class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


# ============================================
# User Schemas
# ============================================

class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    display_name: Optional[str] = Field(None, max_length=255)
    role: UserRoleEnum = UserRoleEnum.VIEWER
    is_active: bool = True


class UserCreate(UserBase):
    """User creation schema."""
    password: Optional[str] = Field(None, min_length=6)


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    display_name: Optional[str] = Field(None, max_length=255)
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)


class UserResponse(UserBase):
    """User response schema."""
    id: UUID
    is_ldap_user: bool
    last_login: Optional[datetime]
    created_at: datetime
    groups: List["GroupBasic"] = []
    
    model_config = ConfigDict(from_attributes=True)


class UserBasic(BaseModel):
    """Basic user info for references."""
    id: UUID
    username: str
    display_name: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class CurrentUser(BaseModel):
    """Current authenticated user."""
    id: UUID
    username: str
    email: Optional[str]
    display_name: Optional[str]
    role: UserRoleEnum
    groups: List[str] = []
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# Group Schemas
# ============================================

class GroupBase(BaseModel):
    """Base group schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class GroupCreate(GroupBase):
    """Group creation schema."""
    ldap_dn: Optional[str] = None
    parent_group_ids: List[UUID] = []


class GroupUpdate(BaseModel):
    """Group update schema."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    parent_group_ids: Optional[List[UUID]] = None


class GroupResponse(GroupBase):
    """Group response schema."""
    id: UUID
    ldap_dn: Optional[str]
    created_at: datetime
    user_count: int = 0
    child_groups: List["GroupBasic"] = []
    
    model_config = ConfigDict(from_attributes=True)


class GroupBasic(BaseModel):
    """Basic group info for references."""
    id: UUID
    name: str
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# Replay Schemas
# ============================================

class ReplayBase(BaseModel):
    """Base replay schema."""
    session_name: Optional[str] = Field(None, max_length=255)
    owner_username: Optional[str] = Field(None, max_length=100)
    client_ip: Optional[str] = Field(None, max_length=45)


class ReplayCreate(ReplayBase):
    """Replay creation (internal use)."""
    filename: str
    original_path: str
    stored_path: str
    file_size: int = 0
    duration_seconds: int = 0
    session_start: Optional[datetime] = None
    session_end: Optional[datetime] = None
    metadata_json: dict = {}


class ReplayUpdate(BaseModel):
    """Replay update schema."""
    session_name: Optional[str] = Field(None, max_length=255)
    status: Optional[ReplayStatusEnum] = None


class ReplayResponse(ReplayBase):
    """Replay response schema."""
    id: UUID
    filename: str
    file_size: int
    duration_seconds: int
    session_start: Optional[datetime]
    session_end: Optional[datetime]
    imported_at: datetime
    status: ReplayStatusEnum
    protocol: Optional[str] = None
    hostname: Optional[str] = None
    connection_name: Optional[str] = None
    storage_tier: StorageTierEnum = StorageTierEnum.HOT
    owner: Optional[UserBasic] = None
    
    model_config = ConfigDict(from_attributes=True)


class ReplayDetail(ReplayResponse):
    """Detailed replay response."""
    original_path: Optional[str]
    stored_path: Optional[str]
    metadata_json: dict = {}
    created_at: datetime
    updated_at: datetime


class ReplaySearch(BaseModel):
    """Replay search filters."""
    query: Optional[str] = None
    username: Optional[str] = None
    session_name: Optional[str] = None
    client_ip: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[ReplayStatusEnum] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None
    protocol: Optional[str] = None
    hostname: Optional[str] = None
    storage_tier: Optional[StorageTierEnum] = None


# ============================================
# Audit Schemas
# ============================================

class AuditLogResponse(BaseModel):
    """Audit log response schema."""
    id: UUID
    user_id: Optional[UUID]
    username: Optional[str]
    replay_id: Optional[UUID]
    action: AuditActionEnum
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: dict = {}
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogSearch(BaseModel):
    """Audit log search filters."""
    user_id: Optional[UUID] = None
    username: Optional[str] = None
    replay_id: Optional[UUID] = None
    action: Optional[AuditActionEnum] = None
    ip_address: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class AuditExportRequest(BaseModel):
    """Audit export request."""
    format: str = Field(default="csv", pattern="^(csv|json)$")
    filters: Optional[AuditLogSearch] = None


# ============================================
# Statistics Schemas
# ============================================

class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_replays: int
    total_users: int
    total_storage_bytes: int
    replays_today: int
    replays_this_week: int
    active_sessions: int


class TopUser(BaseModel):
    """Top user by replay count."""
    username: str
    display_name: Optional[str]
    replay_count: int
    total_duration_seconds: int


class StorageStats(BaseModel):
    """Storage statistics."""
    total_bytes: int
    used_bytes: int
    available_bytes: int
    replay_count_by_status: dict


class ReplayStats(BaseModel):
    """Replay statistics over time."""
    date: str
    count: int
    total_duration_seconds: int


# ============================================
# Pagination Schemas
# ============================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================
# System Settings Schemas
# ============================================

class SystemSettingResponse(BaseModel):
    """System setting response."""
    key: str
    value: Optional[str]
    description: Optional[str]
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SystemSettingUpdate(BaseModel):
    """System setting update."""
    value: str


# ============================================
# Health Check
# ============================================

class HealthCheck(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    database: str = "connected"
    timestamp: datetime


# Update forward references
UserResponse.model_rebuild()
GroupResponse.model_rebuild()
