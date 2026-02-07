"""
Nachos Replay for Guaca - Configuration
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Nachos Replay for Guaca"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "dev-secret-key-change-in-production"
    
    # Database
    database_url: str = "postgresql://nachos:nachos_secret@localhost:5432/nachos_replay"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    
    # JWT
    jwt_secret_key: str = "dev-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # LDAP
    ldap_enabled: bool = False
    ldap_server: str = ""
    ldap_base_dn: str = ""
    ldap_bind_dn: str = ""
    ldap_bind_password: str = ""
    ldap_user_search_base: str = ""
    ldap_group_search_base: str = ""
    ldap_user_attr_username: str = "sAMAccountName"
    ldap_user_attr_email: str = "mail"
    ldap_user_attr_display_name: str = "displayName"
    
    # Guacamole
    guacamole_recordings_path: str = "/guacamole/recordings"
    replay_storage_path: str = "/app/replays"
    replay_import_delay_hours: int = 24
    
    # Storage
    retention_days: int = 365
    max_storage_gb: int = 500
    archive_enabled: bool = True
    archive_compression: str = "gzip"
    
    # Security
    cors_origins: str = "http://localhost,http://localhost:5173"
    allowed_hosts: str = "localhost,127.0.0.1"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        return [host.strip() for host in self.allowed_hosts.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
