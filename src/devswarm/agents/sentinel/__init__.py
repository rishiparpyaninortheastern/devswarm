"""Fingerprinting preserves semantic numbers while removing known volatile identifiers."""

import hashlib
import json
import re

from devswarm.shared.contracts import Incident

FINGERPRINT_VERSION = "v2"


def normalize(value: str) -> str:
    value = re.sub(r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b", "<id>", value)
    value = re.sub(
        r"(?i)\b\d+(?:\.\d+)?\s*(?:milliseconds?|ms|seconds?|secs?|s|minutes?|mins?)\b",
        "<duration>",
        value,
    )
    value = re.sub(r"(\.[A-Za-z]{1,8}:)\d+\b", r"\1<line>", value)
    return re.sub(
        r"(?i)(\b(?:request|trace|correlation)[_-]?id\s*[:=]\s*)[A-Za-z0-9_-]+",
        r"\1<id>",
        value,
    )


def fingerprint(incident: Incident) -> str:
    # Status codes, numeric error codes, ports and business values remain significant.
    fields = [
        FINGERPRINT_VERSION,
        incident.service,
        incident.environment,
        incident.exception_type,
        normalize(incident.message),
        *map(normalize, incident.stack),
    ]
    return hashlib.sha256(json.dumps(fields, ensure_ascii=True).encode()).hexdigest()
