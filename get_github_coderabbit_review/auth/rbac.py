"""Role-Based Access Control (RBAC) system for enterprise authentication."""

import functools
import ipaddress
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class PermissionType(Enum):
    """Permission type enumeration."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"
    CREATE = "create"
    UPDATE = "update"
    APPROVE = "approve"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_AUDIT = "view_audit"
    EXPORT_DATA = "export_data"


class ResourceType(Enum):
    """Resource type enumeration."""

    ANALYSIS = "analysis"
    COMMENT = "comment"
    REPORT = "report"
    DASHBOARD = "dashboard"
    CONFIGURATION = "configuration"
    USER = "user"
    ROLE = "role"
    AUDIT_LOG = "audit_log"
    API_KEY = "api_key"
    SYSTEM = "system"


@dataclass
class Permission:
    """Permission definition."""

    id: str
    name: str
    permission_type: PermissionType
    resource_type: ResourceType
    description: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Post-initialization validation."""
        if not self.id:
            self.id = str(uuid.uuid4())

    def matches_request(
        self, request_permission: PermissionType, request_resource: ResourceType
    ) -> bool:
        """Check if permission matches request.

        Args:
            request_permission: Requested permission type
            request_resource: Requested resource type

        Returns:
            True if permission matches
        """
        # Admin permission grants all access
        if self.permission_type == PermissionType.ADMIN:
            return True

        # Exact match
        if self.permission_type == request_permission and self.resource_type == request_resource:
            return True

        # Write permission includes read
        if (
            self.permission_type == PermissionType.WRITE
            and request_permission == PermissionType.READ
            and self.resource_type == request_resource
        ):
            return True

        return False

    def evaluate_conditions(self, context: Dict[str, Any]) -> bool:
        """Evaluate permission conditions.

        Args:
            context: Evaluation context

        Returns:
            True if conditions are met
        """
        if not self.conditions:
            return True

        for condition, expected_value in self.conditions.items():
            context_value = context.get(condition)

            if condition == "time_of_day":
                current_hour = datetime.now().hour
                if isinstance(expected_value, dict):
                    start_hour = int(expected_value.get("start", 0))
                    end_hour = int(expected_value.get("end", 23))
                    if start_hour <= end_hour:
                        if not (start_hour <= current_hour <= end_hour):
                            return False
                    else:
                        # overnight window (e.g., 22-6)
                        if not (current_hour >= start_hour or current_hour <= end_hour):
                            return False

            elif condition == "ip_range":
                # CIDR-aware IP range check
                user_ip = context.get("ip_address")
                try:
                    ip_obj = ipaddress.ip_address(user_ip)  # type: ignore[arg-type]
                    networks = (
                        expected_value
                        if isinstance(expected_value, (list, tuple))
                        else [expected_value]
                    )
                    if not any(ip_obj in ipaddress.ip_network(n) for n in networks):
                        return False
                except Exception:
                    logger.warning(
                        "Invalid IP/range in condition: ip=%s expected=%s", user_ip, expected_value
                    )
                    return False

            elif condition == "department":
                user_department = context.get("department", "")
                if isinstance(expected_value, (list, tuple, set)):
                    if user_department not in expected_value:
                        return False
                elif isinstance(expected_value, str):
                    if user_department != expected_value:
                        return False
                else:
                    logger.warning(
                        "Unsupported 'department' expected_value type: %s", type(expected_value)
                    )
                    return False

            elif context_value != expected_value:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "permission_type": self.permission_type.value,
            "resource_type": self.resource_type.value,
            "description": self.description,
            "conditions": self.conditions,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Role:
    """Role definition."""

    id: str
    name: str
    description: str = ""
    permissions: List[Permission] = field(default_factory=list)
    parent_roles: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Post-initialization validation."""
        if not self.id:
            self.id = str(uuid.uuid4())

    def add_permission(self, permission: Permission) -> None:
        """Add permission to role.

        Args:
            permission: Permission to add
        """
        # Check for duplicates
        for existing in self.permissions:
            if existing.id == permission.id:
                return

        self.permissions.append(permission)
        self.updated_at = datetime.now()
        logger.info(f"Added permission {permission.name} to role {self.name}")

    def remove_permission(self, permission_id: str) -> bool:
        """Remove permission from role.

        Args:
            permission_id: Permission ID to remove

        Returns:
            True if permission was removed
        """
        initial_count = len(self.permissions)
        self.permissions = [p for p in self.permissions if p.id != permission_id]

        if len(self.permissions) < initial_count:
            self.updated_at = datetime.now()
            logger.info(f"Removed permission {permission_id} from role {self.name}")
            return True

        return False

    def has_permission(
        self,
        permission_type: PermissionType,
        resource_type: ResourceType,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check if role has specific permission.

        Args:
            permission_type: Permission type to check
            resource_type: Resource type to check
            context: Optional context for condition evaluation

        Returns:
            True if role has permission
        """
        if not self.active:
            return False

        context = context or {}

        for permission in self.permissions:
            if permission.matches_request(permission_type, resource_type):
                if permission.evaluate_conditions(context):
                    return True

        return False

    def get_all_permissions(self, rbac_manager: "RBACManager") -> List[Permission]:
        """Get all permissions including inherited from parent roles.

        Args:
            rbac_manager: RBAC manager instance

        Returns:
            List of all permissions
        """
        all_permissions = self.permissions.copy()

        # Add permissions from parent roles
        for parent_role_id in self.parent_roles:
            parent_role = rbac_manager.get_role(parent_role_id)
            if parent_role:
                all_permissions.extend(parent_role.permissions)

        # Remove duplicates
        unique_permissions = {}
        for perm in all_permissions:
            unique_permissions[perm.id] = perm

        return list(unique_permissions.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": [p.to_dict() for p in self.permissions],
            "parent_roles": self.parent_roles,
            "metadata": self.metadata,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class User:
    """User definition."""

    id: str
    username: str
    email: str
    full_name: str = ""
    roles: List[str] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Post-initialization validation."""
        if not self.id:
            self.id = str(uuid.uuid4())

    def add_role(self, role_id: str) -> None:
        """Add role to user.

        Args:
            role_id: Role ID to add
        """
        if role_id not in self.roles:
            self.roles.append(role_id)
            self.updated_at = datetime.now()
            logger.info(f"Added role {role_id} to user {self.username}")

    def remove_role(self, role_id: str) -> bool:
        """Remove role from user.

        Args:
            role_id: Role ID to remove

        Returns:
            True if role was removed
        """
        if role_id in self.roles:
            self.roles.remove(role_id)
            self.updated_at = datetime.now()
            logger.info(f"Removed role {role_id} from user {self.username}")
            return True

        return False

    def has_role(self, role_id: str) -> bool:
        """Check if user has specific role.

        Args:
            role_id: Role ID to check

        Returns:
            True if user has role
        """
        return role_id in self.roles

    def get_context(self) -> Dict[str, Any]:
        """Get user context for permission evaluation.

        Returns:
            User context dictionary
        """
        context = {
            "user_id": self.id,
            "username": self.username,
            "email": self.email,
            "groups": self.groups,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        context.update(self.attributes)
        return context

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "roles": self.roles,
            "groups": self.groups,
            "attributes": self.attributes,
            "active": self.active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class AccessControlList:
    """Access Control List for specific resources."""

    resource_id: str
    resource_type: ResourceType
    permissions: Dict[str, List[PermissionType]] = field(
        default_factory=dict
    )  # user_id -> permissions
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def grant_permission(self, user_id: str, permission: PermissionType) -> None:
        """Grant permission to user.

        Args:
            user_id: User ID
            permission: Permission to grant
        """
        if user_id not in self.permissions:
            self.permissions[user_id] = []

        if permission not in self.permissions[user_id]:
            self.permissions[user_id].append(permission)
            self.updated_at = datetime.now()
            logger.info(
                f"Granted {permission.value} permission on {self.resource_id} to user {user_id}"
            )

    def revoke_permission(self, user_id: str, permission: PermissionType) -> bool:
        """Revoke permission from user.

        Args:
            user_id: User ID
            permission: Permission to revoke

        Returns:
            True if permission was revoked
        """
        if user_id in self.permissions and permission in self.permissions[user_id]:
            self.permissions[user_id].remove(permission)
            if not self.permissions[user_id]:
                del self.permissions[user_id]

            self.updated_at = datetime.now()
            logger.info(
                f"Revoked {permission.value} permission on {self.resource_id} from user {user_id}"
            )
            return True

        return False

    def has_permission(self, user_id: str, permission: PermissionType) -> bool:
        """Check if user has permission.

        Args:
            user_id: User ID
            permission: Permission to check

        Returns:
            True if user has permission
        """
        user_permissions = self.permissions.get(user_id, [])
        return permission in user_permissions or PermissionType.ADMIN in user_permissions


class PolicyEngine:
    """Policy evaluation engine."""

    def __init__(self) -> None:
        """Initialize policy engine."""
        self.policies: Dict[str, Dict[str, Any]] = {}

    def add_policy(self, policy_id: str, policy: Dict[str, Any]) -> None:
        """Add security policy.

        Args:
            policy_id: Policy identifier
            policy: Policy definition
        """
        self.policies[policy_id] = policy
        logger.info(f"Added security policy: {policy_id}")

    def evaluate_policy(self, policy_id: str, context: Dict[str, Any]) -> bool:
        """Evaluate security policy.

        Args:
            policy_id: Policy identifier
            context: Evaluation context

        Returns:
            True if policy passes
        """
        policy = self.policies.get(policy_id)
        if not policy:
            logger.warning("Policy not found: %s", policy_id)
            return False

        try:
            # Simple policy evaluation (expand for production)
            conditions = policy.get("conditions", {})

            for condition, expected in conditions.items():
                if condition == "max_failed_logins":
                    failed_logins = context.get("failed_logins", 0)
                    if failed_logins > expected:
                        return False

                elif condition == "session_timeout":
                    session_start = context.get("session_start")
                    if session_start:
                        session_age = datetime.now() - session_start
                        if session_age.total_seconds() > expected:
                            return False

                elif condition == "require_mfa":
                    mfa_verified = context.get("mfa_verified", False)
                    if expected and not mfa_verified:
                        return False

            return True

        except Exception:
            logger.exception("Policy evaluation error")
            return False


class RBACManager:
    """Role-Based Access Control Manager."""

    def __init__(self) -> None:
        """Initialize RBAC manager."""
        self.users: Dict[str, User] = {}
        self.roles: Dict[str, Role] = {}
        self.permissions: Dict[str, Permission] = {}
        self.acls: Dict[str, AccessControlList] = {}
        self.policy_engine = PolicyEngine()

        # Initialize default roles and permissions
        self._init_default_roles()

    def _policy_allows(self, context: Dict[str, Any]) -> bool:
        """Evaluate zero or more policy IDs from context. Empty -> allow."""
        policies = context.get("policies") or context.get("policy_id")
        if not policies:
            return True
        if isinstance(policies, str):
            policies = [policies]
        for pid in policies:
            if not self.policy_engine.evaluate_policy(pid, context):
                return False
        return True

    def _init_default_roles(self) -> None:
        """Initialize default roles and permissions."""
        # Admin permissions
        admin_permissions = [
            Permission(
                id="admin_all",
                name="Administrator All Access",
                permission_type=PermissionType.ADMIN,
                resource_type=ResourceType.SYSTEM,
                description="Full system access",
            )
        ]

        # User permissions
        user_permissions = [
            Permission(
                id="read_analysis",
                name="Read Analysis",
                permission_type=PermissionType.READ,
                resource_type=ResourceType.ANALYSIS,
                description="View analysis results",
            ),
            Permission(
                id="read_comment",
                name="Read Comments",
                permission_type=PermissionType.READ,
                resource_type=ResourceType.COMMENT,
                description="View comments",
            ),
            Permission(
                id="read_dashboard",
                name="Read Dashboard",
                permission_type=PermissionType.READ,
                resource_type=ResourceType.DASHBOARD,
                description="View dashboard",
            ),
        ]

        # Analyst permissions
        analyst_permissions = user_permissions + [
            Permission(
                id="write_analysis",
                name="Write Analysis",
                permission_type=PermissionType.WRITE,
                resource_type=ResourceType.ANALYSIS,
                description="Create and modify analysis",
            ),
            Permission(
                id="export_data",
                name="Export Data",
                permission_type=PermissionType.EXPORT_DATA,
                resource_type=ResourceType.REPORT,
                description="Export reports and data",
            ),
        ]

        # Store permissions
        for perm in admin_permissions + user_permissions + analyst_permissions:
            self.permissions[perm.id] = perm

        # Create default roles
        admin_role = Role(
            id="admin",
            name="Administrator",
            description="System administrator with full access",
            permissions=admin_permissions,
        )

        analyst_role = Role(
            id="analyst",
            name="Analyst",
            description="Code analysis specialist",
            permissions=analyst_permissions,
        )

        user_role = Role(
            id="user",
            name="User",
            description="Standard user with read access",
            permissions=user_permissions,
        )

        self.roles[admin_role.id] = admin_role
        self.roles[analyst_role.id] = analyst_role
        self.roles[user_role.id] = user_role

        logger.info("Initialized default RBAC roles and permissions")

    def create_user(self, username: str, email: str, full_name: str = "", **kwargs) -> User:
        """Create new user.

        Args:
            username: Username
            email: Email address
            full_name: Full name
            **kwargs: Additional user attributes

        Returns:
            Created user
        """
        user = User(
            id=str(uuid.uuid4()), username=username, email=email, full_name=full_name, **kwargs
        )

        self.users[user.id] = user
        logger.info(f"Created user: {username}")
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User or None
        """
        return self.users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User or None
        """
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    def create_role(
        self, name: str, description: str = "", permissions: Optional[List[Permission]] = None
    ) -> Role:
        """Create new role.

        Args:
            name: Role name
            description: Role description
            permissions: List of permissions

        Returns:
            Created role
        """
        role = Role(
            id=str(uuid.uuid4()), name=name, description=description, permissions=permissions or []
        )

        self.roles[role.id] = role
        logger.info(f"Created role: {name}")
        return role

    def get_role(self, role_id: str) -> Optional[Role]:
        """Get role by ID.

        Args:
            role_id: Role ID

        Returns:
            Role or None
        """
        return self.roles.get(role_id)

    def assign_role(self, user_id: str, role_id: str) -> bool:
        """Assign role to user.

        Args:
            user_id: User ID
            role_id: Role ID

        Returns:
            True if role was assigned
        """
        user = self.get_user(user_id)
        role = self.get_role(role_id)

        if user and role:
            user.add_role(role_id)
            return True

        return False

    def check_permission(
        self,
        user_id: str,
        permission_type: PermissionType,
        resource_type: ResourceType,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check if user has permission.

        Args:
            user_id: User ID
            permission_type: Permission type
            resource_type: Resource type
            resource_id: Optional specific resource ID
            context: Optional context for evaluation

        Returns:
            True if user has permission
        """
        user = self.get_user(user_id)
        if not user or not user.active:
            return False

        # Merge user context
        eval_context = user.get_context()
        if context:
            eval_context.update(context)

        # Check role-based permissions including inheritance
        for role_id in user.roles:
            role = self.get_role(role_id)
            if role:
                # Check direct permissions
                if role.has_permission(permission_type, resource_type, eval_context):
                    return self._policy_allows(eval_context)

                # Check inherited permissions from parent roles
                all_permissions = role.get_all_permissions(self)
                for permission in all_permissions:
                    if permission.matches_request(permission_type, resource_type):
                        if permission.evaluate_conditions(eval_context):
                            return self._policy_allows(eval_context)

        # Check ACL permissions for specific resources
        if resource_id:
            acl_key = f"{resource_type.value}:{resource_id}"
            acl = self.acls.get(acl_key)
            if acl and acl.has_permission(user_id, permission_type):
                return self._policy_allows(eval_context)

        return False

    def create_acl(self, resource_id: str, resource_type: ResourceType) -> AccessControlList:
        """Create Access Control List for resource.

        Args:
            resource_id: Resource identifier
            resource_type: Resource type

        Returns:
            Created ACL
        """
        acl_key = f"{resource_type.value}:{resource_id}"
        acl = AccessControlList(resource_id=resource_id, resource_type=resource_type)

        self.acls[acl_key] = acl
        logger.info(f"Created ACL for {acl_key}")
        return acl

    def grant_resource_permission(
        self,
        user_id: str,
        resource_id: str,
        resource_type: ResourceType,
        permission: PermissionType,
    ) -> bool:
        """Grant permission on specific resource.

        Args:
            user_id: User ID
            resource_id: Resource ID
            resource_type: Resource type
            permission: Permission to grant

        Returns:
            True if permission was granted
        """
        acl_key = f"{resource_type.value}:{resource_id}"

        if acl_key not in self.acls:
            self.create_acl(resource_id, resource_type)

        acl = self.acls[acl_key]
        acl.grant_permission(user_id, permission)
        return True

    def get_user_permissions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all permissions for user.

        Args:
            user_id: User ID

        Returns:
            List of permission dictionaries
        """
        user = self.get_user(user_id)
        if not user:
            return []

        all_permissions = []

        # Role-based permissions
        for role_id in user.roles:
            role = self.get_role(role_id)
            if role:
                role_permissions = role.get_all_permissions(self)
                for perm in role_permissions:
                    perm_dict = perm.to_dict()
                    perm_dict["source"] = f"role:{role.name}"
                    all_permissions.append(perm_dict)

        # ACL permissions
        for acl_key, acl in self.acls.items():
            if user_id in acl.permissions:
                for perm_type in acl.permissions[user_id]:
                    all_permissions.append(
                        {
                            "id": f"acl:{acl_key}:{perm_type.value}",
                            "name": f"ACL {perm_type.value} on {acl_key}",
                            "permission_type": perm_type.value,
                            "resource_type": acl.resource_type.value,
                            "source": f"acl:{acl_key}",
                        }
                    )

        return all_permissions

    def get_stats(self) -> Dict[str, Any]:
        """Get RBAC statistics.

        Returns:
            Statistics dictionary
        """
        active_users = sum(1 for user in self.users.values() if user.active)
        active_roles = sum(1 for role in self.roles.values() if role.active)

        return {
            "total_users": len(self.users),
            "active_users": active_users,
            "total_roles": len(self.roles),
            "active_roles": active_roles,
            "total_permissions": len(self.permissions),
            "total_acls": len(self.acls),
        }


# Global RBAC manager
_global_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """Get global RBAC manager."""
    global _global_rbac_manager
    if _global_rbac_manager is None:
        _global_rbac_manager = RBACManager()
    return _global_rbac_manager


def set_rbac_manager(manager: RBACManager) -> None:
    """Set global RBAC manager."""
    global _global_rbac_manager
    _global_rbac_manager = manager
    logger.info("Set global RBAC manager")


# Convenience functions
def check_permission(
    user_id: str,
    permission_type: Union[str, PermissionType],
    resource_type: Union[str, ResourceType],
    resource_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> bool:
    """Check permission using global RBAC manager.

    Args:
        user_id: User ID
        permission_type: Permission type
        resource_type: Resource type
        resource_id: Optional resource ID
        context: Optional context

    Returns:
        True if user has permission
    """
    if isinstance(permission_type, str):
        permission_type = PermissionType(permission_type)
    if isinstance(resource_type, str):
        resource_type = ResourceType(resource_type)

    manager = get_rbac_manager()
    return manager.check_permission(user_id, permission_type, resource_type, resource_id, context)


def require_permission(
    permission_type: Union[str, PermissionType],
    resource_type: Union[str, ResourceType],
    resource_id: Optional[str] = None,
):
    """Decorator to require permission for function access.

    Args:
        permission_type: Required permission type
        resource_type: Required resource type
        resource_id: Optional resource ID

    Returns:
        Decorator function
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get user_id from context (implement based on your auth system)
            user_id = kwargs.get("user_id") or getattr(args[0], "user_id", None)

            if not user_id:
                raise PermissionError("User not authenticated")

            # allow callers to pass request-scoped info: ip_address, department など
            perm_ctx = kwargs.get("permission_context") or kwargs.get("context") or {}
            if not check_permission(user_id, permission_type, resource_type, resource_id, perm_ctx):
                raise PermissionError(
                    f"Insufficient permissions: {permission_type} on {resource_type}"
                )

            return func(*args, **kwargs)

        return wrapper

    return decorator


# Example usage
if __name__ == "__main__":
    # Initialize RBAC
    rbac = RBACManager()

    # Create users
    admin_user = rbac.create_user("admin", "admin@company.com", "System Administrator")
    analyst_user = rbac.create_user("analyst", "analyst@company.com", "Code Analyst")
    regular_user = rbac.create_user("user", "user@company.com", "Regular User")

    # Assign roles
    rbac.assign_role(admin_user.id, "admin")
    rbac.assign_role(analyst_user.id, "analyst")
    rbac.assign_role(regular_user.id, "user")

    # Test permissions
    print(
        f"Admin can manage users: {rbac.check_permission(admin_user.id, PermissionType.MANAGE_USERS, ResourceType.USER)}"
    )
    print(
        f"Analyst can write analysis: {rbac.check_permission(analyst_user.id, PermissionType.WRITE, ResourceType.ANALYSIS)}"
    )
    print(
        f"User can read dashboard: {rbac.check_permission(regular_user.id, PermissionType.READ, ResourceType.DASHBOARD)}"
    )
    print(
        f"User can delete analysis: {rbac.check_permission(regular_user.id, PermissionType.DELETE, ResourceType.ANALYSIS)}"
    )

    # Print stats
    print(f"RBAC Stats: {rbac.get_stats()}")
