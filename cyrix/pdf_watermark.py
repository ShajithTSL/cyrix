import io
import re
import frappe
import frappe.utils.pdf as frappe_pdf
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

STAMP_MARKER_RE = re.compile(r'id="stamp-marker"[^>]*data-company="([^"]*)"')


def _resolve_file_path(file_url: str):
    if not file_url:
        return None
    if file_url.startswith("/private/files/"):
        return frappe.get_site_path("private", "files", file_url.split("/private/files/", 1)[-1])
    if file_url.startswith("/files/"):
        return frappe.get_site_path("public", "files", file_url.split("/files/", 1)[-1])
    try:
        return frappe.get_doc("File", {"file_url": file_url}).get_full_path()
    except frappe.DoesNotExistError:
        return None


def _get_stamp_for_company(company: str):
    if not company or not frappe.db.exists("Stamp", {"company":company}):
        return None
    stamp = frappe.get_cached_doc("Stamp", {"company":company})
    if not stamp.get("is_active", 1):
        return None
    return stamp


def _stamp_pdf_bytes(pdf_bytes: bytes, stamp) -> bytes:
    image_path = _resolve_file_path(stamp.stamp_image)
    if not image_path:
        return pdf_bytes

    width_pt = stamp.width_pt or 110
    x_pt = stamp.x_pt or 0
    y_pt = stamp.y_pt or 0
    rotation = stamp.rotation or 0
    opacity = (stamp.opacity or 62) / 100

    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    img = ImageReader(image_path)
    iw, ih = img.getSize()
    height_pt = width_pt * ih / iw

    for page in reader.pages:
        page_w = float(page.mediabox.width)
        page_h = float(page.mediabox.height)

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(page_w, page_h))
        c.saveState()
        c.setFillAlpha(opacity)
        c.translate(x_pt + width_pt / 2, y_pt + height_pt / 2)
        c.rotate(rotation)
        c.drawImage(
            img,
            -width_pt / 2, -height_pt / 2,
            width=width_pt, height=height_pt,
            mask="auto",
        )
        c.restoreState()
        c.save()
        buf.seek(0)

        page.merge_page(PdfReader(buf).pages[0])
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


_original_get_pdf = frappe_pdf.get_pdf


def patched_get_pdf(*args, **kwargs):
    html = args[0] if args else kwargs.get("html", "")
    result = _original_get_pdf(*args, **kwargs)

    if not isinstance(result, (bytes, bytearray)):
        return result

    match = STAMP_MARKER_RE.search(html or "")
    if not match:
        return result

    try:
        stamp = _get_stamp_for_company(match.group(1))
        if stamp:
            result = _stamp_pdf_bytes(result, stamp)
    except Exception:
        frappe.log_error(title="Stamp watermark failed")

    return result


frappe_pdf.get_pdf = patched_get_pdf