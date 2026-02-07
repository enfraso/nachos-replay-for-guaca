-- Initialize database schema
-- This file is run automatically when the PostgreSQL container starts

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE user_role AS ENUM ('admin', 'viewer', 'auditor');
CREATE TYPE replay_status AS ENUM ('active', 'archived', 'deleted');
CREATE TYPE audit_action AS ENUM ('view', 'download', 'search', 'login', 'logout', 'export', 'create', 'update', 'delete');

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    display_name VARCHAR(255),
    password_hash VARCHAR(255),
    ldap_dn VARCHAR(500),
    role user_role DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT true,
    is_ldap_user BOOLEAN DEFAULT false,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Groups table
CREATE TABLE IF NOT EXISTS groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    ldap_dn VARCHAR(500),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Group hierarchy (for RBAC)
CREATE TABLE IF NOT EXISTS group_hierarchy (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    child_group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    UNIQUE(parent_group_id, child_group_id)
);

-- User-Group association
CREATE TABLE IF NOT EXISTS user_groups (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, group_id)
);

-- Replays table
CREATE TABLE IF NOT EXISTS replays (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(500) UNIQUE NOT NULL,
    original_path VARCHAR(1000),
    stored_path VARCHAR(1000),
    session_name VARCHAR(255),
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    owner_username VARCHAR(100),
    client_ip VARCHAR(45),
    file_size BIGINT DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,
    session_start TIMESTAMP WITH TIME ZONE,
    session_end TIMESTAMP WITH TIME ZONE,
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status replay_status DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs table (immutable)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(100),
    replay_id UUID REFERENCES replays(id) ON DELETE SET NULL,
    action audit_action NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System settings table
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Token blacklist (for logout)
CREATE TABLE IF NOT EXISTS token_blacklist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_jti VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_replays_owner_id ON replays(owner_id);
CREATE INDEX IF NOT EXISTS idx_replays_owner_username ON replays(owner_username);
CREATE INDEX IF NOT EXISTS idx_replays_status ON replays(status);
CREATE INDEX IF NOT EXISTS idx_replays_session_start ON replays(session_start);
CREATE INDEX IF NOT EXISTS idx_replays_imported_at ON replays(imported_at);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_replay_id ON audit_logs(replay_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_user_groups_user_id ON user_groups(user_id);
CREATE INDEX IF NOT EXISTS idx_user_groups_group_id ON user_groups(group_id);

CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires ON token_blacklist(expires_at);

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, display_name, password_hash, role, is_active)
VALUES (
    'admin',
    'admin@nachos.local',
    'Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.CQvqvLPjvP5Kze',
    'admin',
    true
) ON CONFLICT (username) DO NOTHING;

-- Insert test users
INSERT INTO users (username, email, display_name, password_hash, role, is_active)
VALUES 
    ('viewer', 'viewer@nachos.local', 'Test Viewer', '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'viewer', true),
    ('auditor', 'auditor@nachos.local', 'Test Auditor', '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'auditor', true)
ON CONFLICT (username) DO NOTHING;

-- Insert default settings
INSERT INTO system_settings (key, value, description)
VALUES 
    ('retention_days', '365', 'Number of days to retain replays before archiving'),
    ('max_storage_gb', '500', 'Maximum storage in GB before cleanup'),
    ('import_delay_hours', '24', 'Hours to wait before importing new replays'),
    ('archive_compression', 'gzip', 'Compression algorithm for archived replays')
ON CONFLICT (key) DO NOTHING;
