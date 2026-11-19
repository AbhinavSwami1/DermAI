from app.services.prediction_utils import top_n_predictions
from app.services.report_service import build_csv, build_json, build_pdf

REC = {
    "prediction_id": "p1", "case_id": "c1", "image_id": "i1",
    "original_filename": "a.png", "analysis_timestamp": "2026-11-19T10:00:00+00:00",
    "model_name": "M", "model_version": "v1", "architecture": "A",
    "predicted_label": "NEV", "confidence": 0.61,
    "class_scores": {"NEV": 0.61, "ACK": 0.2, "BCC": 0.1, "MEL": 0.05, "SCC": 0.03, "SEK": 0.01},
    "status": "completed", "image_quality": None,
}
REC["top_predictions"] = top_n_predictions(REC["class_scores"], 3)


def test_top3_sorted_and_sized():
    top = REC["top_predictions"]
    assert [t["class_name"] for t in top] == ["NEV", "ACK", "BCC"]
    assert top_n_predictions({"A": 1.0}, 3)[0]["rank"] == 1
    assert top_n_predictions(None) == []


def test_exports_match_record():
    assert b'"p1"' in build_json(REC)
    assert b"NEV" in build_csv(REC) and b"limitation" in build_csv(REC)
    assert build_pdf(REC, None, None)[:4] == b"%PDF"
