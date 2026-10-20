import re

from devswarm.shared.contracts import Incident

PATTERNS = [
    (r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+", r"\1[REDACTED]"),
    (r"(?i)((?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]"),
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]"),
    (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[IP]"),
    (r"https?://[^\s]+", "[URL]"),
]


def redact(text: str) -> str:
    for pattern, replacement in PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


def sanitize(incident: Incident) -> Incident:
    return incident.model_copy(
        update={
            "message": redact(incident.message),
            "stack": [redact(s[:1000]) for s in incident.stack],
        }
    )
