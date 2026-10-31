from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.security import hash_password
from app.models import User, Role, UserRole
from app.schemas import UserCreate, UserResponse


router = APIRouter(prefix="/api/v1/users", tags=["Users"])


# PUBLIC USER REGISTRATION
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    try:
        # Find the default Patient role
        patient_role = db.scalar(
            select(Role).where(Role.role_name == "Patient")
        )

        # Create the role if it does not exist
        if patient_role is None:
            patient_role = Role(
                role_name="Patient",
                description="Standard user with access to their own cases.",
            )
            db.add(patient_role)
            db.flush()

        # Create the user
        new_user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            full_name=user_data.full_name,
        )

        db.add(new_user)
        db.flush()

        # Assign Patient role
        user_role = UserRole(
            user_id=new_user.user_id,
            role_id=patient_role.role_id,
        )

        db.add(user_role)

        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to register user. Email or role may already exist.",
        )

    return new_user


# PROTECTED CURRENT USER PROFILE
@router.get(
    "/me",
    response_model=UserResponse,
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user