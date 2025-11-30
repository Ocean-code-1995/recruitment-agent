"""Document parser utilities."""

from .text import normalize_bullets, tag_contacts, EMAIL_RE, PHONE_RE, URL_RE
from .image import render_pdf_to_images, pil_to_png_data_uri, split_halves
from .sections import (
    parse_sections_from_json_text,
    normalize_sections,
    merge_duplicate_titles,
    build_contact_section_from_filename,
    process_section,
    apply_postprocessing,
)

__all__ = [
    # Text
    "normalize_bullets",
    "tag_contacts",
    "EMAIL_RE",
    "PHONE_RE",
    "URL_RE",
    # Image
    "render_pdf_to_images",
    "pil_to_png_data_uri",
    "split_halves",
    # Sections
    "parse_sections_from_json_text",
    "normalize_sections",
    "merge_duplicate_titles",
    "build_contact_section_from_filename",
    "process_section",
    "apply_postprocessing",
]

