from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import Case, User
from app.schemas import CaseResponse

router = APIRouter(prefix="/api/v1", tags=["Cases"])


# CREATE CASE — authenticated user only
@router.post(
    "/cases",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_case(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_case = Case(owner_id=current_user.user_id)

    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    return new_case


# GET ALL CASES — own cases only
@router.get(
    "/users/{owner_id}/cases",
    response_model=list[CaseResponse],
)
def get_user_cases(
    owner_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access another user's cases.",
        )

    return db.scalars(
        select(Case)
        .where(Case.owner_id == current_user.user_id)
        .order_by(Case.created_at.desc())
    ).all()


# GET SINGLE CASE — owner only
@router.get(
    "/cases/{case_id}",
    response_model=CaseResponse,
)
def get_case(
    case_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case = db.scalar(
        select(Case).where(
            Case.case_id == case_id,
            Case.owner_id == current_user.user_id,
        )
    )

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found.",
        )

    return case