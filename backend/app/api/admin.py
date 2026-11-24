from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.core.database import get_db
from app.models import Role, User, UserRole

router = APIRouter(prefix="/api/v1/admin", tags=["Administration"])

RoleName = Literal["Patient", "Dermatologist", "Medical Researcher", "Data Scientist", "Administrator"]


@router.get("/users")
def list_users(
    _: User = Depends(require_roles("Administrator")),
    db: Session = Depends(get_db),
):
    """List registered users with their roles (administrator only)."""
    users = db.scalars(select(User).order_by(User.created_at.desc()).limit(200)).all()
    pairs = db.execute(
        select(UserRole.user_id, Role.role_name).join(Role, Role.role_id == UserRole.role_id)
    ).all()
    roles: dict = {}
    for user_id, name in pairs:
        roles.setdefault(user_id, []).append(name)
    return {
        "users": [
            {
                "user_id": str(u.user_id),
                "email": u.email,
                "full_name": u.full_name,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
                "roles": sorted(roles.get(u.user_id, [])),
            }
            for u in users
        ]
    }


@router.delete("/users/{user_id}/roles/{role_name}")
def revoke_role(
    user_id: UUID,
    role_name: RoleName,
    current_user: User = Depends(require_roles("Administrator")),
    db: Session = Depends(get_db),
):
    """Remove one role from a user (administrator only)."""
    if user_id == current_user.user_id and role_name == "Administrator":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot remove their own Administrator role.",
        )
    role = db.scalar(select(Role).where(Role.role_name == role_name))
    assignment = (
        db.scalar(select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role.role_id))
        if role else None
    )
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role assignment not found.")
    try:
        db.execute(delete(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role.role_id))
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to remove the role.")
    remaining = db.scalars(
        select(Role.role_name).join(UserRole, UserRole.role_id == Role.role_id).where(UserRole.user_id == user_id)
    ).all()
    return {"user_id": str(user_id), "roles": sorted(remaining)}
