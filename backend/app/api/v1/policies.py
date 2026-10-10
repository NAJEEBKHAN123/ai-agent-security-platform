from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_role
from app.models.policy import Policy
from app.models.user import User, UserRole

router = APIRouter(prefix="/policies", tags=["Security Policies"])


class PolicyResponse(BaseModel):
    id: int
    name: str
    tool_name: str
    allowed_role: UserRole
    is_enabled: bool
    requires_approval: bool
    description: str
    model_config = ConfigDict(from_attributes=True)


class PolicyUpdate(BaseModel):
    is_enabled: bool
    allowed_role: UserRole
    requires_approval: bool


@router.get("", response_model=List[PolicyResponse])
def get_all_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Retrieve all tool access control policies and permission constraints."""
    return db.query(Policy).order_by(Policy.id.asc()).all()


@router.patch("/{policy_id}", response_model=PolicyResponse)
def update_policy_configuration(
    policy_id: int,
    policy_in: PolicyUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role([UserRole.ADMIN]))
) -> Any:
    """Update a security policy's status, role requirement, or approval setting (Admin Only)."""
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy with ID {policy_id} not found."
        )

    policy.is_enabled = policy_in.is_enabled
    policy.allowed_role = policy_in.allowed_role
    policy.requires_approval = policy_in.requires_approval
    db.commit()
    db.refresh(policy)
    return policy
