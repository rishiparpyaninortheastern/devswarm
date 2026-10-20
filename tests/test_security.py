"""Regression cases for real intake-boundary defects found during the overnight audit."""

import json

import pytest
from pydantic import ValidationError

from devswarm import DevSwarm, Incident
from devswarm.agents.guardian import redact


@pytest.mark.parametrize(
    "text",
    [
        'password="synthetic secret phrase"',
        "password='synthetic secret phrase'",
        '{"token": "synthetic secret phrase"}',
        '{"api_key":"synthetic-secret"}',
        "Authorization: Basic c3ludGhldGljOnNlY3JldA==",
        '{"Authorization": "Bearer synthetic-secret"}',
        "access_token=synthetic-secret",
        "client_secret=synthetic-secret",
        "AccountKey=synthetic-secret;",
        "SharedAccessKey=synthetic-secret;",
    ],
)
def test_quoted_and_structured_credentials_redacted(text):
    safe = redact(text)
    assert "[REDACTED]" in safe
    assert "synthetic" not in safe
    assert "c3ludGhldGlj" not in safe
    assert "phrase" not in safe


def payload():
    return {
        "service": "checkout",
        "environment": "local",
        "exception_type": "TimeoutError",
        "message": "sanitized failure",
        "occurred_at": "2026-10-20T00:00:00Z",
        "stack": [],
        "sanitized": True,
    }


@pytest.mark.parametrize("value", [1, 1.0, "true", False, None])
def test_sanitized_assertion_requires_boolean_true(value):
    with pytest.raises(ValidationError):
        Incident.model_validate(payload() | {"sanitized": value})


def test_oversized_stack_rejected_before_sanitization():
    with pytest.raises(ValidationError):
        Incident.model_validate(payload() | {"stack": ["x" * 1001]})


def test_sdk_revalidates_constructed_models(tmp_path):
    unvalidated = Incident.model_construct(**(payload() | {"sanitized": False}))
    sdk = DevSwarm(tmp_path / "invalid.db")
    with pytest.raises(ValidationError):
        sdk.ingest(unvalidated)
    with sdk.store.connect() as db:
        assert db.execute("SELECT count(*) FROM incidents").fetchone()[0] == 0


def test_json_redaction_preserves_structure():
    assert json.loads(redact('{"token": "synthetic secret phrase"}')) == {"token": "[REDACTED]"}


def test_safe_message_unchanged():
    text = "checkout request timed out; inspect reserve_inventory"
    assert redact(text) == text


def test_expanding_redaction_remains_processable(tmp_path):
    sdk = DevSwarm(tmp_path / "expansion.db")
    incident = payload() | {"message": "token=x " * 490, "stack": ["token=x " * 125]}
    receipt = sdk.ingest(incident)
    assert sdk.process_next()
    draft = sdk.get(receipt.fingerprint)["draft"]
    assert len(draft["evidence"][0]["excerpt"]) <= 4000
    assert len(draft["evidence"][1]["excerpt"]) <= 1000
    assert "token=x" not in json.dumps(draft)


def test_structured_credentials_removed_before_persistence(tmp_path):
    sdk = DevSwarm(tmp_path / "structured.db")
    incident = payload() | {
        "message": '{"token": "synthetic secret phrase"}',
        "stack": ["Authorization: Basic c3ludGhldGljOnNlY3JldA=="],
    }
    receipt = sdk.ingest(incident)
    assert sdk.process_next()
    draft = sdk.get(receipt.fingerprint)["draft"]
    assert json.loads(draft["evidence"][0]["excerpt"]) == {"token": "[REDACTED]"}
    for secret in (b"synthetic secret phrase", b"c3ludGhldGlj"):
        assert secret not in (tmp_path / "structured.db").read_bytes()
