"""
Nachos Replay for Guaca - SQLAlchemy Models
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
import enum

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, BigInteger,
    ForeignKey, Text, Enum, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    VIEWER = "viewer"
    AUDITOR = "auditor"


class ReplayStatus(str, enum.Enum):
    """Replay status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class AuditAction(str, enum.Enum):
    """Audit action enumeration."""
    VIEW = "view"
    DOWNLOAD = "download"
    SEARCH = "search"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


# Association table for user-group many-to-many
class UserGroup(Base):
    """User-Group association table."""
    __tablename__ = "user_groups"
    
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    group_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        primary_key=True
    )


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    ldap_dn: Mapped[Optional[str]] = mapped_column(String(500))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_type=False),
        default=UserRole.VIEWER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_ldap_user: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    groups: Mapped[List["Group"]] = relationship(
        "Group",
        secondary="user_groups",
        back_populates="users"
    )
    replays: Mapped[List["Replay"]] = relationship(
        "Replay",
        back_populates="owner"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user"
    )


class Group(Base):
    """Group model for RBAC."""
    __tablename__ = "groups"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    ldap_dn: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_groups",
        back_populates="groups"
    )
    parent_groups: Mapped[List["Group"]] = relationship(
        "Group",
        secondary="group_hierarchy",
        primaryjoin="Group.id == GroupHierarchy.child_group_id",
        secondaryjoin="Group.id == GroupHierarchy.parent_group_id",
        back_populates="child_groups"
    )
    child_groups: Mapped[List["Group"]] = relationship(
        "Group",
        secondary="group_hierarchy",
        primaryjoin="Group.id == GroupHierarchy.parent_group_id",
        secondaryjoin="Group.id == GroupHierarchy.child_group_id",
        back_populates="parent_groups"
    )


class GroupHierarchy(Base):
    """Group hierarchy for nested permissions."""
    __tablename__ = "group_hierarchy"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    parent_group_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE")
    )
    child_group_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE")
    )
    
    __table_args__ = (
        UniqueConstraint("parent_group_id", "child_group_id"),
    )


class Replay(Base):
    """Replay recording model."""
    __tablename__ = "replays"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    filename: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    original_path: Mapped[Optional[str]] = mapped_column(String(1000))
    stored_path: Mapped[Optional[str]] = mapped_column(String(1000))
    session_name: Mapped[Optional[str]] = mapped_column(String(255))
    owner_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    owner_username: Mapped[Optional[str]] = mapped_column(String(100))
    client_ip: Mapped[Optional[str]] = mapped_column(String(45))
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    session_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    session_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    status: Mapped[ReplayStatus] = mapped_column(
        Enum(ReplayStatus, name="replay_status", create_type=False),
        default=ReplayStatus.ACTIVE
    )
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    owner: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="replays"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="replay"
    )
    
    __table_args__ = (
        Index("idx_replays_owner_username", "owner_username"),
        Index("idx_replays_status", "status"),
        Index("idx_replays_session_start", "session_start"),
    )


class AuditLog(Base):
    """Audit log model (immutable)."""
    __tablename__ = "audit_logs"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    username: Mapped[Optional[str]] = mapped_column(String(100))
    replay_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("replays.id", ondelete="SET NULL")
    )
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action", create_type=False),
        nullable=False
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs"
    )
    replay: Mapped[Optional["Replay"]] = relationship(
        "Replay",
        back_populates="audit_logs"
    )
    
    __table_args__ = (
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_created_at", "created_at"),
    )


class SystemSetting(Base):
    """System settings model."""
    __tablename__ = "system_settings"
    
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class TokenBlacklist(Base):
    """Token blacklist for logout."""
    __tablename__ = "token_blacklist"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    token_jti: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
