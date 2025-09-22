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
    # Core authentication (required)
    "User",
    "Role",
    "Permission",
    "RBACManager",
    "SessionManager",
    "AuditLogger",

    # Basic providers (standard)
    "SSOProvider",
    "SSOManager",

    # Enterprise features (optional)
    # Import explicitly if needed
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
