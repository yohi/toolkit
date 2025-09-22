"""Enterprise authentication module for CodeRabbit fetcher."""

from .sso import (
    SSOProvider,
    SSOConfig,
    SSOManager,
    OAuthProvider,
    SAMLProvider,
    OpenIDConnectProvider
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

from .ldap import (
    LDAPConnector,
    LDAPConfig,
    UserManager,
    GroupManager,
    DirectorySync
)

from .session import (
    SessionManager,
    SessionConfig,
    TokenManager,
    JWTProvider,
    RefreshTokenHandler
)

__all__ = [
    # SSO
    "SSOProvider",
    "SSOConfig",
    "SSOManager",
    "OAuthProvider",
    "SAMLProvider",
    "OpenIDConnectProvider",

    # RBAC
    "RBACManager",
    "Role",
    "Permission",
    "User",
    "AccessControlList",
    "PolicyEngine",

    # Audit
    "AuditLogger",
    "AuditEvent",
    "AuditConfig",
    "ComplianceReporter",
    "SecurityAnalyzer",

    # LDAP
    "LDAPConnector",
    "LDAPConfig",
    "UserManager",
    "GroupManager",
    "DirectorySync",

    # Session Management
    "SessionManager",
    "SessionConfig",
    "TokenManager",
    "JWTProvider",
    "RefreshTokenHandler"
]
