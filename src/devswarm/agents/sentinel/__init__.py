import hashlib
import json
import re

from devswarm.shared.contracts import Incident


def normalize(value: str) -> str:
    value = re.sub(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}\b", "<id>", value)
    return re.sub(r"\b\d+\b", "<n>", value)


def fingerprint(incident: Incident) -> str:
    # Include message and stack: unrelated failures of the same type must not collapse.
    fields = [
        incident.service,
        incident.environment,
        incident.exception_type,
        normalize(incident.message),
        *map(normalize, incident.stack),
    ]
    return hashlib.sha256(json.dumps(fields, ensure_ascii=True).encode()).hexdigest()
