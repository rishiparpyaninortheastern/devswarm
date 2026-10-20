"""Best-effort defensive redaction after strict incident-boundary validation."""

import re

from devswarm.shared.contracts import Incident

CREDENTIAL = re.compile(
    r"""(?ix)
    (?P<label>
      (?<![\w-])["']?
      (?:authorization|password|passwd|secret|token|api[_-]?key|
         access[_-]?token|refresh[_-]?token|client[_-]?secret|
         account[_-]?key|sharedaccesskey)
      ["']?\s*[:=]\s*
    )
    (?P<value>
      "(?:\\.|[^"\\])*"
      | '(?:\\.|[^'\\])*'
      | (?:bearer|basic)\s+[^\s,;}]+
      | [^\s,;}]+
    )
    """
)
PATTERNS = [
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]"),
    (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[IP]"),
    (r"""(?i)https?://[^\s<>"']+""", "[URL]"),
]


def _hide_credential(match: re.Match) -> str:
    value = match.group("value")
    quote = value[0] if value[0] in {"'", '"'} else ""
    return match.group("label") + quote + "[REDACTED]" + quote


def redact(text: str) -> str:
    text = CREDENTIAL.sub(_hide_credential, text)
    for pattern, replacement in PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


def sanitize(incident: Incident) -> Incident:
    # Pydantic instances can be built with model_construct/model_copy, bypassing validation.
    # Revalidate at the trust boundary before persistence, even for SDK callers.
    incident = Incident.model_validate(incident)
    # Redaction markers can expand short values. Bound only after redaction so we never
    # persist a partial credential, and keep the sanitized record valid for worker retries.
    values = incident.model_dump()
    values["message"] = redact(incident.message)[:4000]
    values["stack"] = [redact(line)[:1000] for line in incident.stack]
    return Incident.model_validate(values)
