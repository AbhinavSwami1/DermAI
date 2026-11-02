from math import ceil
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import (
    Case,
    Image as ImageModel,
    ImageQualityAssessment,
    ModelVersion,
    Prediction,
    User,
)
from app.schemas import (
    PredictionResponse,
    PredictionHistoryItem,
    PredictionHistoryResponse,
)
from app.services.image_validation import (
    ImageValidationError,
    validate_image,
)
from app.services.inference_service import (
    InferenceError,
    predict_image,
)
from app.services.gradcam_service import generate_gradcam


router = APIRouter(
    prefix="/api/v1/predictions",
    tags=["Predictions"],
)

STORAGE_DIR = (
    Path(__file__).resolve().parents[2]
    / "storage"
    / "original"
)

MODEL_NAME = "DermAI MobileNetV3-Large Fine-tuned"
MODEL_VERSION = "mobilenet_v3_large_finetuned_epoch9"
MODEL_ARCHITECTURE = "MobileNetV3-Large"

CHECKPOINT_REFERENCE = (
    "ml/checkpoints/mobilenet/best_mobilenet_v3_large_finetuned.pth"
)

DISCLAIMER = (
    "Research prototype output only. This prediction is not a "
    "medical diagnosis and must not be used for clinical decisions."
)

QUALITY_DISCLAIMER = (
    "Image quality assessment uses preliminary research heuristics. "
    "It is not clinically validated."
)


def get_owned_image(
    image_id: UUID,
    current_user: User,
    db: Session,
):
    """Retrieve an image only if it belongs to the authenticated user."""

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

    return image_record


def get_acceptable_quality_assessment(
    image_id: UUID,
    db: Session,
):
    """Require an acceptable quality assessment before AI processing."""

    assessment = db.scalar(
        select(ImageQualityAssessment)
        .where(
            ImageQualityAssessment.image_id == image_id,
        )
        .order_by(
            ImageQualityAssessment.assessed_at.desc(),
            ImageQualityAssessment.assessment_id.desc(),
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "QUALITY_ASSESSMENT_MISSING",
                "message": (
                    "Image quality assessment is unavailable. "
                    "Please upload the image again."
                ),
            },
        )

    if assessment.quality_status != "ACCEPTABLE":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "IMAGE_REVIEW_REQUIRED",
                "message": (
                    "This image requires quality review before "
                    "prediction. Please replace it with a clearer "
                    "image or review the quality warnings."
                ),
                "quality_status": assessment.quality_status,
                "quality_flags": assessment.quality_flags,
                "algorithm_version": assessment.algorithm_version,
                "disclaimer": QUALITY_DISCLAIMER,
            },
        )

    return assessment


def get_safe_image_bytes(image_record: ImageModel) -> bytes:
    """Read and validate an image stored inside configured storage."""

    storage_root = STORAGE_DIR.resolve()
    image_path = (
        storage_root / image_record.storage_key
    ).resolve()

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

    return image_bytes


# --------------------------------------------------
# PREDICTION HISTORY
# --------------------------------------------------

@router.get(
    "/history",
    response_model=PredictionHistoryResponse,
    status_code=status.HTTP_200_OK,
)
def get_prediction_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return paginated prediction history belonging to the
    authenticated user only.
    """

    ownership_filter = (
        select(Prediction.prediction_id)
        .join(
            ImageModel,
            Prediction.image_id == ImageModel.image_id,
        )
        .join(
            Case,
            ImageModel.case_id == Case.case_id,
        )
        .where(
            Case.owner_id == current_user.user_id,
        )
    )

    total = db.scalar(
        select(func.count()).select_from(
            ownership_filter.subquery()
        )
    ) or 0

    total_pages = ceil(total / page_size) if total else 0

    history_query = (
        select(
            Prediction,
            ImageModel,
            Case,
            ModelVersion,
        )
        .join(
            ImageModel,
            Prediction.image_id == ImageModel.image_id,
        )
        .join(
            Case,
            ImageModel.case_id == Case.case_id,
        )
        .join(
            ModelVersion,
            Prediction.model_version_id
            == ModelVersion.model_version_id,
        )
        .where(
            Case.owner_id == current_user.user_id,
        )
        .order_by(
            Prediction.created_at.desc(),
            Prediction.prediction_id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    records = db.execute(history_query).all()

    items = [
        PredictionHistoryItem(
            prediction_id=prediction.prediction_id,
            case_id=case.case_id,
            image_id=image.image_id,
            original_filename=image.original_filename,
            predicted_label=prediction.predicted_label,
            confidence=prediction.confidence,
            class_scores=prediction.class_scores,
            status=prediction.status,
            model_version_id=model.model_version_id,
            model_name=model.model_name,
            model_version=model.version,
            architecture=model.architecture,
            created_at=prediction.created_at,
        )
        for prediction, image, case, model in records
    ]

    return PredictionHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        disclaimer=DISCLAIMER,
    )


# --------------------------------------------------
# CREATE PREDICTION
# --------------------------------------------------

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
    image_record = get_owned_image(
        image_id,
        current_user,
        db,
    )

    image_bytes = get_safe_image_bytes(image_record)

    get_acceptable_quality_assessment(
        image_record.image_id,
        db,
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


# --------------------------------------------------
# GRAD-CAM
# --------------------------------------------------

@router.post(
    "/{image_id}/gradcam",
    response_class=Response,
    status_code=status.HTTP_200_OK,
)
def create_gradcam_visualization(
    image_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image_record = get_owned_image(
        image_id,
        current_user,
        db,
    )

    image_bytes = get_safe_image_bytes(image_record)

    get_acceptable_quality_assessment(
        image_record.image_id,
        db,
    )

    try:
        visualization = generate_gradcam(image_bytes)

    except InferenceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Grad-CAM visualization is currently unavailable.",
        )

    return Response(
        content=visualization,
        media_type="image/png",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Research-Disclaimer": (
                "Research visualization only; not a medical diagnosis."
            ),
        },
    )