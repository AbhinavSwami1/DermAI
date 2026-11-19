from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.core.database import get_db
from app.models import Case, Image as ImageModel, ModelVersion, Prediction, User

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboards"])

# Display-only heuristic for "score below threshold"; NOT a clinical rule.
LOW_SCORE_THRESHOLD = 0.5


@router.get("/clinician")
def clinician_dashboard(
    _: User = Depends(require_roles("Dermatologist", "Administrator")),
    db: Session = Depends(get_db),
):
    total_cases = db.scalar(select(func.count()).select_from(Case)) or 0
    total_preds = db.scalar(select(func.count()).select_from(Prediction)) or 0
    dist = db.execute(
        select(Prediction.predicted_label, func.count())
        .group_by(Prediction.predicted_label)
    ).all()
    avg_conf = db.scalar(select(func.avg(Prediction.confidence)))
    low = db.scalar(
        select(func.count()).select_from(Prediction)
        .where(Prediction.confidence < LOW_SCORE_THRESHOLD)
    ) or 0
    recent = db.execute(
        select(Prediction, ImageModel)
        .join(ImageModel, Prediction.image_id == ImageModel.image_id)
        .order_by(Prediction.created_at.desc()).limit(10)
    ).all()
    return {
        "total_cases": total_cases,
        "total_analyses": total_preds,
        "average_model_score": float(avg_conf) if avg_conf is not None else None,
        "low_score_threshold": LOW_SCORE_THRESHOLD,
        "low_score_analyses": low,
        "predicted_class_distribution": {k: v for k, v in dist},
        "recent_analyses": [
            {"prediction_id": str(p.prediction_id), "case_id": str(i.case_id),
             "predicted_label": p.predicted_label, "confidence": p.confidence,
             "created_at": p.created_at.isoformat()}
            for p, i in recent
        ],
        "note": "Model scores are not clinically validated probabilities.",
    }


@router.get("/admin")
def admin_dashboard(
    _: User = Depends(require_roles("Administrator")),
    db: Session = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=7)
    usage = db.execute(
        select(ModelVersion.model_name, ModelVersion.version, func.count(Prediction.prediction_id))
        .join(Prediction, Prediction.model_version_id == ModelVersion.model_version_id, isouter=True)
        .group_by(ModelVersion.model_name, ModelVersion.version)
    ).all()
    return {
        "registered_users": db.scalar(select(func.count()).select_from(User)) or 0,
        "total_cases": db.scalar(select(func.count()).select_from(Case)) or 0,
        "total_images": db.scalar(select(func.count()).select_from(ImageModel)) or 0,
        "total_analyses": db.scalar(select(func.count()).select_from(Prediction)) or 0,
        "analyses_last_7_days": db.scalar(
            select(func.count()).select_from(Prediction).where(Prediction.created_at >= since)
        ) or 0,
        "model_usage": [{"model_name": n, "version": v, "analyses": c} for n, v, c in usage],
    }
