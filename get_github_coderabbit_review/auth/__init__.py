"""Enterprise authentication module for CodeRabbit fetcher."""

from .audit import AuditConfig, AuditEvent, AuditLogger, ComplianceReporter, SecurityAnalyzer
from .rbac import AccessControlList, Permission, PolicyEngine, RBACManager, Role, User
from .session import JWTProvider, RefreshTokenHandler, SessionConfig, SessionManager, TokenManager
from .sso import OAuthProvider, SSOConfig, SSOManager, SSOProvider

# LDAP imports handled in try/except block below for optional dependency


__all__ = [
    # Sorted alphabetically for RUF022 compliance
    "AccessControlList",
    "AuditConfig",
    "AuditEvent",
    "AuditLogger",
    "ComplianceReporter",
    "JWTProvider",
    "OAuthProvider",
    "Permission",
    "PolicyEngine",
    "RBACManager",
    "RefreshTokenHandler",
    "Role",
    "SSOConfig",
    "SSOManager",
    "SSOProvider",
    "SecurityAnalyzer",
    "SessionConfig",
    "SessionManager",
    "TokenManager",
    "User",
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

    __all__.extend(["OpenIDConnectProvider", "SAMLProvider"])
except ImportError:
    # 高度なSSO機能はオプション
    pass
