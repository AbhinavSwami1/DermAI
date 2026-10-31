from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_roles
from app.core.database import get_db
from app.models import Role, User, UserRole
from app.schemas import RoleAssignmentRequest, UserRoleResponse

router = APIRouter(prefix="/api/v1/roles", tags=["Role Management"])


# GET CURRENT USER ROLES
@router.get("/me", response_model=UserRoleResponse)
def get_my_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    roles = db.scalars(
        select(Role.role_name)
        .join(UserRole, UserRole.role_id == Role.role_id)
        .where(UserRole.user_id == current_user.user_id)
    ).all()

    return UserRoleResponse(
        user_id=current_user.user_id,
        roles=list(roles),
    )


# ADMINISTRATOR-ONLY ROLE ASSIGNMENT
@router.post(
    "/users/{user_id}",
    response_model=UserRoleResponse,
    status_code=status.HTTP_200_OK,
)
def assign_role(
    user_id: UUID,
    role_data: RoleAssignmentRequest,
    current_user: User = Depends(require_roles("Administrator")),
    db: Session = Depends(get_db),
):
    target_user = db.scalar(
        select(User).where(User.user_id == user_id)
    )

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    role = db.scalar(
        select(Role).where(Role.role_name == role_data.role_name)
    )

    try:
        if role is None:
            role = Role(
                role_name=role_data.role_name,
                description=f"{role_data.role_name} role.",
            )
            db.add(role)
            db.flush()

        existing_assignment = db.scalar(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role.role_id,
            )
        )

        if existing_assignment is None:
            db.add(
                UserRole(
                    user_id=user_id,
                    role_id=role.role_id,
                )
            )

        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to assign the requested role.",
        )

    assigned_roles = db.scalars(
        select(Role.role_name)
        .join(UserRole, UserRole.role_id == Role.role_id)
        .where(UserRole.user_id == user_id)
    ).all()

    return UserRoleResponse(
        user_id=user_id,
        roles=list(assigned_roles),
    )