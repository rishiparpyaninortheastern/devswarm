"""Allowlisted operational logs. Never attach telemetry or exception messages."""

import json
import logging

logger = logging.getLogger("devswarm.operations")


def record(event: str, **fields: str | int | bool) -> None:
    allowed = {
        key: value
        for key, value in fields.items()
        if key in {"fingerprint", "occurrences", "duplicate", "state"}
    }
    logger.info(json.dumps({"event": event, **allowed}, sort_keys=True))
