"""Enterprise authentication module for CodeRabbit fetcher."""

from .sso import (
    SSOProvider,
    SSOConfig,
    SSOManager,
    OAuthProvider,
)

from .rbac import (
    RBACManager,
    Role,
    Permission,
    User,
    AccessControlList,
    PolicyEngine
)

from .audit import (
    AuditLogger,
    AuditEvent,
    AuditConfig,
    ComplianceReporter,
    SecurityAnalyzer
)

# LDAP imports handled in try/except block below for optional dependency

from .session import (
    SessionManager,
    SessionConfig,
    TokenManager,
    JWTProvider,
    RefreshTokenHandler
)

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
    from .sso import SAMLProvider, OpenIDConnectProvider
    __all__.extend(["SAMLProvider", "OpenIDConnectProvider"])
except ImportError:
    # 高度なSSO機能はオプション
    pass
