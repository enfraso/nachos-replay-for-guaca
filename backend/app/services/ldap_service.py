"""
Nachos Replay for Guaca - LDAP Service
Handles Active Directory / LDAP authentication and group synchronization.
"""
import logging
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LDAPUser:
    """LDAP user data."""
    username: str
    email: Optional[str]
    display_name: Optional[str]
    dn: str
    groups: List[str]


class LDAPService:
    """Service for LDAP/Active Directory operations."""
    
    def __init__(self):
        self.enabled = settings.ldap_enabled
        self._connection = None
    
    def _get_connection(self):
        """Get LDAP connection (lazy initialization)."""
        if not self.enabled:
            return None
        
        if self._connection is None:
            try:
                import ldap
                self._connection = ldap.initialize(settings.ldap_server)
                self._connection.protocol_version = ldap.VERSION3
                self._connection.simple_bind_s(
                    settings.ldap_bind_dn,
                    settings.ldap_bind_password
                )
            except Exception as e:
                logger.error(f"LDAP connection failed: {e}")
                raise
        
        return self._connection
    
    def authenticate(self, username: str, password: str) -> Optional[LDAPUser]:
        """
        Authenticate user against LDAP/AD.
        Returns LDAPUser if successful, None otherwise.
        """
        if not self.enabled:
            logger.debug("LDAP disabled, falling back to local auth")
            return None
        
        try:
            import ldap
            
            # Search for user
            conn = self._get_connection()
            search_filter = f"({settings.ldap_user_attr_username}={username})"
            
            results = conn.search_s(
                settings.ldap_user_search_base,
                ldap.SCOPE_SUBTREE,
                search_filter,
                [
                    settings.ldap_user_attr_username,
                    settings.ldap_user_attr_email,
                    settings.ldap_user_attr_display_name,
                    "memberOf"
                ]
            )
            
            if not results:
                logger.warning(f"User not found in LDAP: {username}")
                return None
            
            user_dn, user_attrs = results[0]
            
            # Try to bind as the user to verify password
            user_conn = ldap.initialize(settings.ldap_server)
            user_conn.protocol_version = ldap.VERSION3
            
            try:
                user_conn.simple_bind_s(user_dn, password)
            except ldap.INVALID_CREDENTIALS:
                logger.warning(f"Invalid LDAP credentials for: {username}")
                return None
            finally:
                user_conn.unbind_s()
            
            # Extract user info
            def get_attr(attrs: dict, key: str) -> Optional[str]:
                values = attrs.get(key, [])
                if values:
                    return values[0].decode("utf-8") if isinstance(values[0], bytes) else values[0]
                return None
            
            # Extract groups
            groups = []
            member_of = user_attrs.get("memberOf", [])
            for group_dn in member_of:
                if isinstance(group_dn, bytes):
                    group_dn = group_dn.decode("utf-8")
                # Extract CN from DN
                for part in group_dn.split(","):
                    if part.upper().startswith("CN="):
                        groups.append(part[3:])
                        break
            
            return LDAPUser(
                username=get_attr(user_attrs, settings.ldap_user_attr_username) or username,
                email=get_attr(user_attrs, settings.ldap_user_attr_email),
                display_name=get_attr(user_attrs, settings.ldap_user_attr_display_name),
                dn=user_dn,
                groups=groups
            )
            
        except Exception as e:
            logger.error(f"LDAP authentication error: {e}")
            return None
    
    def search_groups(self, search_term: str = "") -> List[Dict]:
        """Search for groups in LDAP."""
        if not self.enabled:
            return []
        
        try:
            import ldap
            
            conn = self._get_connection()
            
            if search_term:
                search_filter = f"(&(objectClass=group)(cn=*{search_term}*))"
            else:
                search_filter = "(objectClass=group)"
            
            results = conn.search_s(
                settings.ldap_group_search_base,
                ldap.SCOPE_SUBTREE,
                search_filter,
                ["cn", "description", "member"]
            )
            
            groups = []
            for dn, attrs in results:
                groups.append({
                    "dn": dn,
                    "name": attrs.get("cn", [b""])[0].decode("utf-8"),
                    "description": attrs.get("description", [b""])[0].decode("utf-8") if attrs.get("description") else None,
                    "member_count": len(attrs.get("member", []))
                })
            
            return groups
            
        except Exception as e:
            logger.error(f"LDAP group search error: {e}")
            return []
    
    def get_group_members(self, group_dn: str) -> List[str]:
        """Get members of an LDAP group."""
        if not self.enabled:
            return []
        
        try:
            import ldap
            
            conn = self._get_connection()
            
            results = conn.search_s(
                group_dn,
                ldap.SCOPE_BASE,
                "(objectClass=*)",
                ["member"]
            )
            
            if not results:
                return []
            
            _, attrs = results[0]
            members = []
            
            for member_dn in attrs.get("member", []):
                if isinstance(member_dn, bytes):
                    member_dn = member_dn.decode("utf-8")
                members.append(member_dn)
            
            return members
            
        except Exception as e:
            logger.error(f"LDAP get group members error: {e}")
            return []
    
    def sync_group_hierarchy(self) -> List[Tuple[str, str]]:
        """
        Sync group hierarchy from AD.
        Returns list of (parent_group_dn, child_group_dn) tuples.
        """
        if not self.enabled:
            return []
        
        try:
            import ldap
            
            conn = self._get_connection()
            
            # Search for all groups
            results = conn.search_s(
                settings.ldap_group_search_base,
                ldap.SCOPE_SUBTREE,
                "(objectClass=group)",
                ["cn", "memberOf"]
            )
            
            hierarchy = []
            for dn, attrs in results:
                parent_groups = attrs.get("memberOf", [])
                for parent_dn in parent_groups:
                    if isinstance(parent_dn, bytes):
                        parent_dn = parent_dn.decode("utf-8")
                    hierarchy.append((parent_dn, dn))
            
            return hierarchy
            
        except Exception as e:
            logger.error(f"LDAP sync hierarchy error: {e}")
            return []
    
    def close(self):
        """Close LDAP connection."""
        if self._connection:
            try:
                self._connection.unbind_s()
            except Exception:
                pass
            self._connection = None


# Mock service for development without LDAP
class MockLDAPService(LDAPService):
    """Mock LDAP service for development/testing."""
    
    MOCK_USERS = {
        "admin": {
            "password": "admin123",
            "email": "admin@nachos.local",
            "display_name": "Administrator",
            "groups": ["Administrators", "IT Department"]
        },
        "viewer": {
            "password": "viewer123",
            "email": "viewer@nachos.local",
            "display_name": "Test Viewer",
            "groups": ["Viewers", "Finance"]
        },
        "auditor": {
            "password": "auditor123",
            "email": "auditor@nachos.local",
            "display_name": "Test Auditor",
            "groups": ["Auditors", "Compliance"]
        }
    }
    
    def authenticate(self, username: str, password: str) -> Optional[LDAPUser]:
        """Mock authentication."""
        user_data = self.MOCK_USERS.get(username.lower())
        
        if not user_data:
            return None
        
        if user_data["password"] != password:
            return None
        
        return LDAPUser(
            username=username.lower(),
            email=user_data["email"],
            display_name=user_data["display_name"],
            dn=f"CN={username},OU=Users,DC=nachos,DC=local",
            groups=user_data["groups"]
        )
    
    def search_groups(self, search_term: str = "") -> List[Dict]:
        """Return mock groups."""
        groups = [
            {"dn": "CN=Administrators,OU=Groups,DC=nachos,DC=local", "name": "Administrators", "member_count": 1},
            {"dn": "CN=Viewers,OU=Groups,DC=nachos,DC=local", "name": "Viewers", "member_count": 1},
            {"dn": "CN=Auditors,OU=Groups,DC=nachos,DC=local", "name": "Auditors", "member_count": 1},
            {"dn": "CN=IT Department,OU=Groups,DC=nachos,DC=local", "name": "IT Department", "member_count": 1},
            {"dn": "CN=Finance,OU=Groups,DC=nachos,DC=local", "name": "Finance", "member_count": 1},
            {"dn": "CN=Compliance,OU=Groups,DC=nachos,DC=local", "name": "Compliance", "member_count": 1},
        ]
        
        if search_term:
            groups = [g for g in groups if search_term.lower() in g["name"].lower()]
        
        return groups


def get_ldap_service() -> LDAPService:
    """Get appropriate LDAP service based on configuration."""
    if settings.ldap_enabled:
        return LDAPService()
    return MockLDAPService()
