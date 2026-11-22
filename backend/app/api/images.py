from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import (
    Case,
    Image as ImageModel,
    ImageQualityAssessment,
    User,
)

router = APIRouter(prefix="/api/v1", tags=["Images"])


@router.get(
    "/images/{image_id}/quality",
    response_model=dict,
)
def get_image_quality(
    image_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessment = db.scalar(
        select(ImageQualityAssessment)
        .join(
            ImageModel,
            ImageQualityAssessment.image_id == ImageModel.image_id,
        )
        .join(Case, ImageModel.case_id == Case.case_id)
        .where(
            ImageQualityAssessment.image_id == image_id,
            Case.owner_id == current_user.user_id,
        )
        .order_by(ImageQualityAssessment.assessed_at.desc())
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image or quality assessment not found.",
        )

    return {
        "image_id": str(assessment.image_id),
        "blur_score": assessment.blur_score,
        "brightness_mean": assessment.brightness_mean,
        "dark_pixel_percentage": assessment.dark_pixel_percentage,
        "bright_pixel_percentage": assessment.bright_pixel_percentage,
        "quality_status": assessment.quality_status,
        "quality_flags": assessment.quality_flags,
        "algorithm_version": assessment.algorithm_version,
        "assessed_at": assessment.assessed_at,
        "disclaimer": (
            "Research-only image quality assessment. "
            "Not clinically validated and not for diagnosis or treatment."
        ),
    }


@router.get("/images/{image_id}/file")
def get_image_file(
    image_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the original stored image (owner only)."""
    from app.api.predictions import get_owned_image, get_safe_image_bytes

    record = get_owned_image(image_id, current_user, db)
    return Response(content=get_safe_image_bytes(record), media_type=record.mime_type)



@router.get("/images/{image_id}/processed")
def get_processed_image(
    image_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the model input (resized, before normalisation) for an owned image."""
    from app.api.predictions import get_owned_image, get_safe_image_bytes
    from app.services.processed_image import render_model_input

    record = get_owned_image(image_id, current_user, db)
    try:
        png, info = render_model_input(get_safe_image_bytes(record))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unable to preprocess the stored image.",
        )
    return Response(
        content=png,
        media_type="image/png",
        headers={"X-Preprocessing-Version": info["version"]},
    )


@router.get("/images/{image_id}/processed/info")
def get_processed_image_info(
    image_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Describe the preprocessing steps applied to an owned image."""
    from app.api.predictions import get_owned_image, get_safe_image_bytes
    from app.services.processed_image import render_model_input

    record = get_owned_image(image_id, current_user, db)
    try:
        _, info = render_model_input(get_safe_image_bytes(record))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unable to preprocess the stored image.",
        )
    return info
