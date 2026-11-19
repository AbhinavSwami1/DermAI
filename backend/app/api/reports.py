from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.predictions import DISCLAIMER, get_safe_image_bytes
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
from app.services.prediction_utils import top_n_predictions
from app.services.report_service import build_csv, build_json, build_pdf

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])

MEDIA = {"json": "application/json", "csv": "text/csv", "pdf": "application/pdf"}


@router.get("/{prediction_id}")
def export_report(
    prediction_id: UUID,
    format: Literal["pdf", "json", "csv"] = Query("pdf"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export a saved analysis (owner only). Built from stored DB values."""
    row = db.execute(
        select(Prediction, ImageModel, Case, ModelVersion)
        .join(ImageModel, Prediction.image_id == ImageModel.image_id)
        .join(Case, ImageModel.case_id == Case.case_id)
        .join(ModelVersion, Prediction.model_version_id == ModelVersion.model_version_id)
        .where(Prediction.prediction_id == prediction_id,
               Case.owner_id == current_user.user_id)
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found.")
    pred, image, case, model = row

    qa = db.scalar(
        select(ImageQualityAssessment)
        .where(ImageQualityAssessment.image_id == image.image_id)
        .order_by(ImageQualityAssessment.assessed_at.desc())
    )
    quality = None
    if qa is not None:
        quality = {
            "quality_status": qa.quality_status,
            "quality_flags": qa.quality_flags,
            "blur_score": qa.blur_score,
            "brightness_mean": qa.brightness_mean,
            "algorithm_version": qa.algorithm_version,
        }

    record = {
        "prediction_id": str(pred.prediction_id),
        "case_id": str(case.case_id),
        "image_id": str(image.image_id),
        "original_filename": image.original_filename,
        "analysis_timestamp": pred.created_at.isoformat(),
        "model_name": model.model_name,
        "model_version": model.version,
        "architecture": model.architecture,
        "predicted_label": pred.predicted_label,
        "confidence": pred.confidence,
        "class_scores": pred.class_scores,
        "top_predictions": top_n_predictions(pred.class_scores, 3),
        "status": pred.status,
        "image_quality": quality,
        "limitation": DISCLAIMER,
    }

    if format == "json":
        data = build_json(record)
    elif format == "csv":
        data = build_csv(record)
    else:
        image_bytes = get_safe_image_bytes(image)
        gradcam_bytes = None
        try:  # Grad-CAM is optional: report must not fail without it
            from app.services.gradcam_service import generate_gradcam
            gradcam_bytes = generate_gradcam(image_bytes)
        except Exception:
            gradcam_bytes = None
        data = build_pdf(record, image_bytes, gradcam_bytes)

    return Response(
        content=data,
        media_type=MEDIA[format],
        headers={"Content-Disposition":
                 f'attachment; filename="dermai_report_{pred.prediction_id}.{format}"'},
    )
