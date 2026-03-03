from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image


def export_story_to_pdf(title: str, scenes: list, pdf_path: str) -> None:
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    # Page titre
    c.setFont("Helvetica-Bold", 22)
    c.drawString(60, height - 80, title)
    c.setFont("Helvetica", 12)
    c.drawString(60, height - 110, "StoryGrow — Livret généré automatiquement")
    c.showPage()

    for sc in scenes:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(60, height - 60, f"Scène {sc['scene_no']}")

        img_path = sc.get("image_path")
        if img_path:
            try:
                img = Image.open(img_path)
                img.thumbnail((420, 420))
                c.drawImage(ImageReader(img), 60, height - 520, width=420, height=420, preserveAspectRatio=True, mask="auto")
            except Exception:
                pass

        c.setFont("Helvetica", 12)
        text_obj = c.beginText(60, height - 560)
        text_obj.setLeading(16)

        for line in _wrap_text(sc.get("text", ""), 80):
            text_obj.textLine(line)

        c.drawText(text_obj)
        c.showPage()

    c.save()


def _wrap_text(text: str, max_len: int):
    words = text.split()
    lines, current, count = [], [], 0

    for w in words:
        if count + len(w) + 1 > max_len:
            lines.append(" ".join(current))
            current, count = [w], len(w)
        else:
            current.append(w)
            count += len(w) + 1

    if current:
        lines.append(" ".join(current))
    return lines