"""Derived notifications. Nothing is stored: every item is computed from the
authenticated user's own saved records, so no alert can be fabricated."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import Case, Image as ImageModel, ImageQualityAssessment, Prediction, User

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

LOW_SCORE_THRESHOLD = 0.5  # display heuristic only, not a clinical rule
LEVEL_ORDER = {"medium": 0, "low": 1, "informational": 2}


@router.get("")
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items: list[dict] = []

    preds = db.execute(
        select(Prediction, ImageModel)
        .join(ImageModel, Prediction.image_id == ImageModel.image_id)
        .join(Case, ImageModel.case_id == Case.case_id)
        .where(Case.owner_id == current_user.user_id)
        .order_by(Prediction.created_at.desc())
        .limit(10)
    ).all()
    for idx, (p, img) in enumerate(preds):
        if idx < 3:
            items.append({
                "id": f"analysis_completed:{p.prediction_id}", "type": "analysis_completed",
                "level": "informational", "title": "Analysis completed",
                "message": f"{img.original_filename}: analysis saved.",
                "created_at": p.created_at.isoformat(), "case_id": str(img.case_id),
            })
        if p.confidence is not None and p.confidence < LOW_SCORE_THRESHOLD:
            items.append({
                "id": f"low_score:{p.prediction_id}", "type": "low_confidence_prediction",
                "level": "medium", "title": "Low model score",
                "message": (f"{img.original_filename}: model score {p.confidence * 100:.1f}% "
                            f"(below {LOW_SCORE_THRESHOLD:.2f}). Professional review is recommended."),
                "created_at": p.created_at.isoformat(), "case_id": str(img.case_id),
            })

    quality = db.execute(
        select(ImageQualityAssessment, ImageModel)
        .join(ImageModel, ImageQualityAssessment.image_id == ImageModel.image_id)
        .join(Case, ImageModel.case_id == Case.case_id)
        .where(Case.owner_id == current_user.user_id,
               ImageQualityAssessment.quality_status != "ACCEPTABLE")
        .order_by(ImageQualityAssessment.assessed_at.desc())
        .limit(5)
    ).all()
    for qa, img in quality:
        items.append({
            "id": f"quality:{qa.assessment_id}", "type": "poor_image_quality",
            "level": "low", "title": ("Image quality warning" if qa.quality_status == "WARNING" else "Image quality review required"),
            "message": f"{img.original_filename}: flagged {', '.join(qa.quality_flags or [])}.",
            "created_at": qa.assessed_at.isoformat(), "case_id": str(img.case_id),
        })

    today = date.today()
    cases = db.scalars(
        select(Case).where(Case.owner_id == current_user.user_id,
                           Case.follow_up_date.is_not(None),
                           Case.follow_up_date <= today + timedelta(days=7))
    ).all()
    for c in cases:
        due = c.follow_up_date <= today
        items.append({
            "id": f"follow_up:{c.case_id}", "type": "follow_up_due" if due else "follow_up_upcoming",
            "level": "medium" if due else "informational",
            "title": "Follow-up due" if due else "Follow-up upcoming",
            "message": f"Case {str(c.case_id)[:8]}: follow-up date {c.follow_up_date.isoformat()}.",
            "created_at": c.updated_at.isoformat(), "case_id": str(c.case_id),
        })

    items.sort(key=lambda i: (LEVEL_ORDER[i["level"]], i["created_at"]), reverse=False)
    return {"count": len(items), "items": items,
            "note": "Alerts are derived from your saved records and are not diagnoses."}
