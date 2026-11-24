import json
from pathlib import Path

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user, require_roles
from app.models import User

router = APIRouter(prefix="/api/v1/insights", tags=["Insights"])

OUTPUT_DIR = Path(__file__).resolve().parents[3] / "ml" / "outputs" / "mobilenet_v3_large_finetuned"


@router.get("/model-info")
def model_info(_: User = Depends(get_current_user)):
    """Deployed model version and class list (any signed-in user)."""
    from app.services.inference_service import CLASS_NAMES, MODEL_VERSION

    return {"model_version": MODEL_VERSION, "class_names": CLASS_NAMES, "num_classes": len(CLASS_NAMES)}


@router.get("/model-metrics")
def model_metrics(
    _: User = Depends(
        require_roles("Medical Researcher", "Data Scientist", "Dermatologist", "Administrator")
    ),
):
    """Saved evaluation metrics (research and staff roles only)."""
    from app.services.inference_service import CLASS_NAMES, MODEL_VERSION

    out = {"available": False, "test_metrics": None, "model_version": MODEL_VERSION,
           "class_names": CLASS_NAMES, "num_classes": len(CLASS_NAMES)}
    f = OUTPUT_DIR / "test_metrics.json"
    if f.is_file():
        out["available"] = True
        out["test_metrics"] = json.loads(f.read_text())
        out["source"] = "ml/outputs/mobilenet_v3_large_finetuned/test_metrics.json"
    return out
