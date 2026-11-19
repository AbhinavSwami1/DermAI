"""Report generation (JSON / CSV / PDF) from a saved analysis record.

All functions are pure: they only format the record they are given.
"""
import csv
import io
import json
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

LIMITATION = (
    "This report is AI-assisted research output and is not a standalone "
    "medical diagnosis. Model scores are softmax outputs and have not been "
    "validated as clinical probabilities. Consult a qualified healthcare "
    "professional for any medical assessment."
)


def build_json(record: dict) -> bytes:
    return json.dumps(record, indent=2, default=str).encode("utf-8")


def build_csv(record: dict) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["section", "field", "value"])
    for key in (
        "prediction_id", "case_id", "image_id", "original_filename",
        "analysis_timestamp", "model_name", "model_version", "architecture",
        "predicted_label", "confidence", "status",
    ):
        w.writerow(["analysis", key, record.get(key, "")])
    for t in record.get("top_predictions", []):
        w.writerow(["top_predictions", f"{t['rank']}:{t['class_name']}", t["score"]])
    for name, score in (record.get("class_scores") or {}).items():
        w.writerow(["class_scores", name, score])
    q = record.get("image_quality") or {}
    for k, v in q.items():
        w.writerow(["image_quality", k, v])
    w.writerow(["limitation", "statement", LIMITATION])
    return buf.getvalue().encode("utf-8")


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(20 * mm, 10 * mm, "DermAI Analysis Report - research prototype")
    canvas.drawRightString(190 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _img(data: bytes | None, max_w_mm: float, max_h_mm: float):
    if not data:
        return None
    try:
        img = RLImage(io.BytesIO(data))
        ratio = min(max_w_mm * mm / img.imageWidth, max_h_mm * mm / img.imageHeight)
        img.drawWidth, img.drawHeight = img.imageWidth * ratio, img.imageHeight * ratio
        return img
    except Exception:
        return None


def build_pdf(record: dict, image_bytes: bytes | None, gradcam_bytes: bytes | None) -> bytes:
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], fontSize=18, alignment=0)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12, spaceBefore=10)
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9, leading=12)
    P = lambda t: Paragraph(escape(str(t)), body)

    def table(rows, widths):
        t = Table([[P(a), P(b)] for a, b in rows] if len(rows[0]) == 2 else
                  [[P(c) for c in r] for r in rows], colWidths=widths)
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        return t

    s = [Paragraph("DermAI Skin-Image Analysis Report", h1),
         Paragraph("AI-assisted research output. Not a medical diagnosis.", body),
         Paragraph("Analysis details", h2)]
    s.append(table([
        ("Case ID", record["case_id"]),
        ("Analysis ID", record["prediction_id"]),
        ("Image file", record["original_filename"]),
        ("Analysis date/time", record["analysis_timestamp"]),
        ("Model", f'{record["model_name"]} ({record["architecture"]})'),
        ("Model version", record["model_version"]),
    ], [45 * mm, 125 * mm]))

    s.append(Paragraph("Prediction", h2))
    s.append(table([
        ("Predicted class", record["predicted_label"]),
        ("Model score", f'{record["confidence"] * 100:.2f}% (softmax output, not a clinical probability)'),
    ], [45 * mm, 125 * mm]))

    rows = [("Rank", "Class", "Model score")] + [
        (t["rank"], t["class_name"], f'{t["score"] * 100:.2f}%')
        for t in record.get("top_predictions", [])
    ]
    s += [Paragraph("Top-3 predictions", h2), table(rows, [20 * mm, 60 * mm, 40 * mm])]

    q = record.get("image_quality")
    s.append(Paragraph("Image quality", h2))
    if q:
        s.append(table([
            ("Status", q.get("quality_status")),
            ("Flags", ", ".join(q.get("quality_flags") or []) or "none"),
            ("Blur score", q.get("blur_score")),
            ("Mean brightness", q.get("brightness_mean")),
            ("Algorithm version", q.get("algorithm_version")),
        ], [45 * mm, 125 * mm]))
    else:
        s.append(P("Image quality record not available."))

    s.append(Paragraph("Images", h2))
    cells = []
    for label, data in (("Original image", image_bytes), ("Grad-CAM overlay", gradcam_bytes)):
        im = _img(data, 80, 80)
        cells.append([P(label), im if im else P("Not available")])
    t = Table([[cells[0][0], cells[1][0]], [cells[0][1], cells[1][1]]], colWidths=[85 * mm, 85 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    s += [t, Spacer(1, 4),
          P("Grad-CAM shows regions influencing the model score. It is not lesion segmentation "
            "and does not show the prediction is correct.")]

    s += [Paragraph("Limitation statement", h2), P(LIMITATION)]

    out = io.BytesIO()
    SimpleDocTemplate(out, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                      topMargin=18 * mm, bottomMargin=18 * mm,
                      title="DermAI Analysis Report").build(s, onFirstPage=_footer, onLaterPages=_footer)
    return out.getvalue()
