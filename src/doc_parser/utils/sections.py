"""Section parsing and processing utilities."""

import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List

from ftfy import fix_text

from .text import normalize_bullets, tag_contacts


def parse_sections_from_json_text(text: str) -> List[Dict[str, str]]:
    """
    Parse STRICT JSON from the API response.
    
    Attempts direct JSON parsing first, then falls back to
    extracting JSON array from surrounding text.
    
    Args:
        text: Raw text that should contain a JSON array.
        
    Returns:
        List of section dicts with 'title' and 'body' keys.
    """
    # Try direct parse
    try:
        data = json.loads(text)
        if isinstance(data, list):
            out: List[Dict[str, str]] = []
            for item in data:
                if isinstance(item, dict):
                    out.append(
                        {
                            "title": str(item.get("title", "")).strip(),
                            "body": str(item.get("body", "")).strip(),
                        }
                    )
            return out
    except Exception:
        pass

    # Try to extract JSON array from text
    m = re.search(r"\[\s*\{[\s\S]*\}\s*\]", text)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, list):
                out: List[Dict[str, str]] = []
                for item in data:
                    if isinstance(item, dict):
                        out.append(
                            {
                                "title": str(item.get("title", "")).strip(),
                                "body": str(item.get("body", "")).strip(),
                            }
                        )
                return out
        except Exception:
            pass
    return []


def normalize_sections(sections: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Normalize text encoding with ftfy (fixes mojibake, etc.)."""
    norm: List[Dict[str, str]] = []
    for s in sections:
        title = fix_text((s.get("title") or "").strip())
        body = fix_text((s.get("body") or "").strip())
        norm.append({"title": title, "body": body})
    return norm


def merge_duplicate_titles(sections: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Merge sections with duplicate titles while preserving order."""
    merged: "OrderedDict[str, str]" = OrderedDict()

    for s in sections:
        title = s.get("title", "").strip()
        body = (s.get("body", "") or "").strip()

        if title in merged:
            if body:
                prev = merged[title]
                merged[title] = (prev + ("\n\n" if prev else "") + body).strip()
        else:
            merged[title] = body

    return [{"title": t, "body": b} for t, b in merged.items()]


def build_contact_section_from_filename(pdf_file: Path) -> Dict[str, str]:
    """
    Create a simple 'Adresse' section based on the PDF filename.
    
    Useful as a fallback when contact info isn't parsed from the document.
    """
    stem = pdf_file.stem.replace("_", " ").strip()
    tokens = stem.split(maxsplit=1)
    if tokens and len(tokens[0]) == 1 and tokens[0].isalpha():
        stem = tokens[1] if len(tokens) > 1 else ""
    name = stem.strip() or pdf_file.name
    return {"title": "Adresse", "body": f"Name: {name}"}


def process_section(section: Dict[str, str]) -> Dict[str, str]:
    """Normalize bullets and tag contact info for a single section."""
    title = section.get("title", "")
    body = section.get("body", "")
    return {
        "title": tag_contacts(normalize_bullets(title)),
        "body": tag_contacts(normalize_bullets(body)),
    }


def apply_postprocessing(sections: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Apply bullet normalization and contact tagging to all sections."""
    return [process_section(s) for s in sections]

