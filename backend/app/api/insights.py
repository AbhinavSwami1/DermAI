import json
from pathlib import Path

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/api/v1/insights", tags=["Insights"])

OUTPUT_DIR = Path(__file__).resolve().parents[3] / "ml" / "outputs" / "mobilenet_v3_large_finetuned"


@router.get("/model-metrics")
def model_metrics(_: User = Depends(get_current_user)):
    """Serve saved evaluation artifacts; nothing is hardcoded."""
    out = {"available": False, "test_metrics": None, "model_version": None}
    f = OUTPUT_DIR / "test_metrics.json"
    if f.is_file():
        out["available"] = True
        out["test_metrics"] = json.loads(f.read_text())
        out["source"] = "ml/outputs/mobilenet_v3_large_finetuned/test_metrics.json"
    from app.services.inference_service import CLASS_NAMES, MODEL_VERSION
    out["model_version"] = MODEL_VERSION
    out["class_names"] = CLASS_NAMES
    out["num_classes"] = len(CLASS_NAMES)
    return out
