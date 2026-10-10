from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.policy import Policy
from app.models.user import User, UserRole


DEFAULT_POLICIES = [
    {
        "name": "Math Computation Policy",
        "tool_name": "safe_calculator",
        "allowed_role": UserRole.USER,
        "is_enabled": True,
        "requires_approval": False,
        "description": "Permits basic arithmetic calculation for all authenticated users.",
    },
    {
        "name": "Internal Policy Summarizer",
        "tool_name": "document_summarizer",
        "allowed_role": UserRole.USER,
        "is_enabled": True,
        "requires_approval": False,
        "description": "Allows retrieval and summarization of approved public security documentation.",
    },
    {
        "name": "Directory & Asset Lookup Policy",
        "tool_name": "record_lookup",
        "allowed_role": UserRole.REVIEWER,
        "is_enabled": True,
        "requires_approval": False,
        "description": "Restricts employee and security asset directory lookups to Reviewers and Administrators.",
    },
    {
        "name": "System Shell Execution Policy",
        "tool_name": "system_shell",
        "allowed_role": UserRole.ADMIN,
        "is_enabled": False,
        "requires_approval": True,
        "description": "Denies arbitrary shell and command-line execution (Denylist baseline).",
    },
]


def init_policies(db: Session):
    """Seed baseline tool security policies if not already present."""
    for p in DEFAULT_POLICIES:
        existing = db.query(Policy).filter(Policy.tool_name == p["tool_name"]).first()
        if not existing:
            new_policy = Policy(
                name=p["name"],
                tool_name=p["tool_name"],
                allowed_role=p["allowed_role"],
                is_enabled=p["is_enabled"],
                requires_approval=p["requires_approval"],
                description=p["description"],
            )
            db.add(new_policy)
    db.commit()


class PolicyDecision:
    def __init__(self, allowed: bool, reason: str, requires_approval: bool = False):
        self.allowed = allowed
        self.reason = reason
        self.requires_approval = requires_approval


class PolicyEngine:
    """Backend access control evaluating tool permissions against RBAC policies."""

    ROLE_HIERARCHY = {
        UserRole.USER: 1,
        UserRole.REVIEWER: 2,
        UserRole.ADMIN: 3,
    }

    def check_tool_permission(self, tool_name: str, user: User, db: Session) -> PolicyDecision:
        """Verify whether the user is authorized by backend policy to invoke the requested tool."""
        policy = db.query(Policy).filter(Policy.tool_name == tool_name).first()

        # If no explicit policy exists, enforce default-deny
        if not policy:
            return PolicyDecision(
                allowed=False,
                reason=f"Default Deny: No security policy found permitting tool '{tool_name}'."
            )

        # Check if policy is disabled
        if not policy.is_enabled:
            return PolicyDecision(
                allowed=False,
                reason=f"Policy Block: Tool '{tool_name}' has been disabled by security policy '{policy.name}'."
            )

        # Evaluate Role Hierarchy (Admin >= Reviewer >= User)
        user_level = self.ROLE_HIERARCHY.get(user.role, 1)
        required_level = self.ROLE_HIERARCHY.get(policy.allowed_role, 3)

        if user_level < required_level:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"Access Denied: Tool '{tool_name}' requires role '{policy.allowed_role.value}', "
                    f"but user has role '{user.role.value}'."
                )
            )

        return PolicyDecision(
            allowed=True,
            reason=f"Tool '{tool_name}' permitted under policy '{policy.name}'.",
            requires_approval=policy.requires_approval,
        )


policy_engine = PolicyEngine()
