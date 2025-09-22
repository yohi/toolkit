"""Enterprise authentication module for CodeRabbit fetcher."""

from .audit import AuditConfig, AuditEvent, AuditLogger, ComplianceReporter, SecurityAnalyzer
from .rbac import AccessControlList, Permission, PolicyEngine, RBACManager, Role, User
from .session import JWTProvider, RefreshTokenHandler, SessionConfig, SessionManager, TokenManager
from .sso import OAuthProvider, SSOConfig, SSOManager, SSOProvider

# LDAP imports handled in try/except block below for optional dependency


__all__ = [
    # Audit
    "AuditConfig",
    "AuditEvent",
    "AuditLogger",
    "ComplianceReporter",
    "SecurityAnalyzer",
    # RBAC
    "AccessControlList",
    "Permission",
    "PolicyEngine",
    "RBACManager",
    "Role",
    "User",
    # Session
    "JWTProvider",
    "RefreshTokenHandler",
    "SessionConfig",
    "SessionManager",
    "TokenManager",
    # SSO (standard)
    "OAuthProvider",
    "SSOConfig",
    "SSOManager",
    "SSOProvider",
]

# エンタープライズ機能の段階的導入
try:
    from .ldap import LDAPConnector

    __all__.extend(["LDAPConnector"])
except ImportError:
    # LDAP機能はオプション
    pass

try:
    from .sso import OpenIDConnectProvider, SAMLProvider

    __all__.extend(["SAMLProvider", "OpenIDConnectProvider"])
except ImportError:
    # 高度なSSO機能はオプション
    pass
