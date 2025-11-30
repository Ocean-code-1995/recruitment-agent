"""Image and PDF rendering utilities."""

import base64
import io
from pathlib import Path
from typing import List

import pypdfium2 as pdfium
from PIL import Image


def render_pdf_to_images(pdf_path: Path, target_width: int = 2000) -> List[Image.Image]:
    """
    Render PDF pages to PIL images (layout-preserving).
    
    Args:
        pdf_path: Path to the PDF file.
        target_width: Target width for rendering (scales proportionally).
        
    Returns:
        List of PIL Image objects, one per page.
    """
    doc = pdfium.PdfDocument(str(pdf_path))
    images: List[Image.Image] = []

    for index in range(len(doc)):
        page = doc[index]
        width_pt, height_pt = page.get_size()
        scale = max(1.0, float(target_width) / float(max(1.0, width_pt)))
        bitmap = page.render(scale=scale)
        img = bitmap.to_pil()
        images.append(img)

    page.close()
    return images


def pil_to_png_data_uri(img: Image.Image) -> str:
    """Convert a PIL image to a PNG data URI (base64)."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def split_halves(img: Image.Image, overlap_px: int = 40) -> List[Image.Image]:
    """
    Create left/right column crops with small overlap.
    
    Useful for two-column CV layouts where GPT-4 Vision might
    miss content in narrow columns.
    
    Args:
        img: PIL Image to split.
        overlap_px: Pixels of overlap in the middle.
        
    Returns:
        List of [left_half, right_half] images.
    """
    w, h = img.size
    mid = w // 2
    left_box = (0, 0, min(mid + overlap_px, w), h)
    right_box = (max(mid - overlap_px, 0), 0, w, h)
    return [img.crop(left_box), img.crop(right_box)]

