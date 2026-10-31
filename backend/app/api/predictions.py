from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import (
    Case,
    Image as ImageModel,
    ModelVersion,
    Prediction,
    User,
)
from app.schemas import PredictionResponse
from app.services.image_validation import (
    ImageValidationError,
    validate_image,
)
from app.services.inference_service import (
    InferenceError,
    predict_image,
)


router = APIRouter(
    prefix="/api/v1/predictions",
    tags=["Predictions"],
)

STORAGE_DIR = (
    Path(__file__).resolve().parents[2]
    / "storage"
    / "original"
)

MODEL_NAME = "DermAI MobileNetV3-Small Baseline"
MODEL_VERSION = "1.0.0-epoch20"
MODEL_ARCHITECTURE = "MobileNetV3-Small"
CHECKPOINT_REFERENCE = (
    "ml/checkpoints/mobilenet/best_mobilenet_v3_small.pth"
)

DISCLAIMER = (
    "Research prototype output only. This prediction is not a "
    "medical diagnosis and must not be used for clinical decisions."
)


@router.post(
    "/{image_id}",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_prediction(
    image_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image_record = db.scalar(
        select(ImageModel)
        .join(Case, ImageModel.case_id == Case.case_id)
        .where(
            ImageModel.image_id == image_id,
            Case.owner_id == current_user.user_id,
        )
    )

    if image_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found.",
        )

    storage_root = STORAGE_DIR.resolve()
    image_path = (storage_root / image_record.storage_key).resolve()

    if not image_path.is_relative_to(storage_root):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image storage reference.",
        )

    try:
        image_bytes = image_path.read_bytes()
        validate_image(image_bytes)
    except (OSError, ImageValidationError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stored image is unavailable or invalid.",
        )

    try:
        inference_result = predict_image(image_bytes)
    except InferenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model inference is currently unavailable.",
        )

    try:
        model_version = db.scalar(
            select(ModelVersion).where(
                ModelVersion.model_name == MODEL_NAME,
                ModelVersion.version == MODEL_VERSION,
                ModelVersion.architecture == MODEL_ARCHITECTURE,
            )
        )

        if model_version is None:
            model_version = ModelVersion(
                model_version_id=uuid4(),
                model_name=MODEL_NAME,
                version=MODEL_VERSION,
                architecture=MODEL_ARCHITECTURE,
                checkpoint_reference=CHECKPOINT_REFERENCE,
            )
            db.add(model_version)
            db.flush()

        prediction = Prediction(
            prediction_id=uuid4(),
            image_id=image_record.image_id,
            model_version_id=model_version.model_version_id,
            predicted_label=inference_result["predicted_label"],
            confidence=inference_result["confidence"],
            class_scores=inference_result["class_scores"],
            status="completed",
        )

        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        db.refresh(model_version)

        return PredictionResponse(
            prediction_id=prediction.prediction_id,
            image_id=prediction.image_id,
            model_version_id=model_version.model_version_id,
            model_name=model_version.model_name,
            model_version=model_version.version,
            architecture=model_version.architecture,
            predicted_label=prediction.predicted_label,
            confidence=prediction.confidence,
            class_scores=prediction.class_scores,
            status=prediction.status,
            created_at=prediction.created_at,
            disclaimer=DISCLAIMER,
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to save prediction.",
        )
