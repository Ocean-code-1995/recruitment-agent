"""Text processing utilities for document parsing."""

import re
from typing import List


# Regex patterns for contact detection
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE_RE = re.compile(r"(?:(?<=\s)|^)(\+\d{1,3}[\s()./-]?)?(?:\d[\s()/.-]?){6,}\d(?=\s|$)")
URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>'\"]+\.[^\s<>'\"]+")

# Bullet characters to normalize
_BULLET_CHARS = {"•", "·", "-", "–", "—", "▪", "◦", "‣", "●", "○", ""}


def normalize_bullets(text: str) -> str:
    """Coerce common bullet characters to '- ' while keeping numbering."""
    lines = text.splitlines()
    normalized: List[str] = []

    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            normalized.append(line)
            continue

        # Keep numbered lists as-is
        if re.match(r"^\d+[\.)]\s+", stripped):
            normalized.append(line)
            continue

        first = stripped[0]
        if first in _BULLET_CHARS or stripped.startswith(("- ", "* ")):
            content = re.sub(
                r"^([\-\*\u2022\u2023\u2043\u2219\u25E6\u25AA\u25CB\u25CF\u25A0]+\s+)", "", stripped
            )
            normalized.append(f"- {content.strip()}")
        else:
            normalized.append(line)

    return "\n".join(normalized)


def tag_contacts(text: str) -> str:
    """Wrap detected email/phone/URL values with simple tags."""
    tagged = EMAIL_RE.sub(lambda m: f"[EMAIL]{m.group(0)}[/EMAIL]", text)
    tagged = PHONE_RE.sub(lambda m: f"[PHONE]{m.group(0)}[/PHONE]", tagged)
    tagged = URL_RE.sub(lambda m: f"[URL]{m.group(0)}[/URL]", tagged)
    return tagged

