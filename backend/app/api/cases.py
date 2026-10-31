from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Case, User
from app.schemas import CaseCreate, CaseResponse

router = APIRouter(prefix="/api/v1", tags=["Cases"])


# CREATE CASE
@router.post(
    "/cases",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_case(
    case_data: CaseCreate,
    db: Session = Depends(get_db),
):
    owner = db.scalar(
        select(User).where(User.user_id == case_data.owner_id)
    )

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    new_case = Case(owner_id=case_data.owner_id)

    db.add(new_case)
    db.commit()
    db.refresh(new_case)

    return new_case


# GET ALL CASES FOR A USER
@router.get(
    "/users/{owner_id}/cases",
    response_model=list[CaseResponse],
)
def get_user_cases(
    owner_id: UUID,
    db: Session = Depends(get_db),
):
    owner = db.scalar(
        select(User).where(User.user_id == owner_id)
    )

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return db.scalars(
        select(Case)
        .where(Case.owner_id == owner_id)
        .order_by(Case.created_at.desc())
    ).all()


# GET SINGLE CASE
@router.get(
    "/cases/{case_id}",
    response_model=CaseResponse,
)
def get_case(
    case_id: UUID,
    db: Session = Depends(get_db),
):
    case = db.scalar(
        select(Case).where(Case.case_id == case_id)
    )

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found.",
        )

    return case