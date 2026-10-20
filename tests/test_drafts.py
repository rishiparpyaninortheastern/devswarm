"""Regression coverage for fingerprint separation and reviewable draft evidence."""

import json
from importlib.resources import files

import pytest
from pydantic import ValidationError

from devswarm import DevSwarm, Incident
from devswarm.agents.sentinel import fingerprint
from devswarm.shared.contracts import BugDraft
from devswarm.shared.llm import LocalDraftProvider


def event(**updates):
    data = json.loads(files("devswarm.resources").joinpath("incident.json").read_text())
    return Incident.model_validate(data | updates)


@pytest.mark.parametrize(
    "left,right",
    [
        ("Upstream returned HTTP 401", "Upstream returned HTTP 503"),
        ("Database error 1205", "Database error 2627"),
        ("Connection refused on port 5432", "Connection refused on port 6432"),
        ("Expected 2 items", "Expected 3 items"),
        ("Unsupported version 1.2.3", "Unsupported version 1.2.4"),
    ],
)
def test_semantic_numbers_do_not_merge(left, right):
    assert fingerprint(event(message=left)) != fingerprint(event(message=right))


@pytest.mark.parametrize(
    "left,right",
    [
        ("Timed out after 3000 ms", "Timed out after 5000 ms"),
        ("Timed out after 1.5 seconds", "Timed out after 3 seconds"),
        ("Failure request_id=123", "Failure request_id=456"),
        ("Failure trace_id=abcdef", "Failure trace_id=fedcba"),
        (
            "Failure 12345678-1234-1234-1234-123456789abc",
            "Failure abcdefab-abcd-abcd-abcd-abcdefabcdef",
        ),
    ],
)
def test_known_volatile_values_merge(left, right):
    assert fingerprint(event(message=left)) == fingerprint(event(message=right))


def test_stack_line_numbers_merge_but_frames_do_not():
    assert fingerprint(event(stack=["checkout.py:42 in reserve"])) == fingerprint(
        event(stack=["checkout.py:87 in reserve"])
    )
    assert fingerprint(event(stack=["checkout.py:42 in reserve"])) != fingerprint(
        event(stack=["checkout.py:42 in refund"])
    )


def test_draft_claims_reference_available_evidence():
    incident = event()
    draft = LocalDraftProvider().generate(incident, fingerprint(incident))
    ids = {item.id for item in draft.evidence}
    assert draft.observations
    for observation in draft.observations:
        assert set(observation.evidence_ids) <= ids
    assert {item.field for item in draft.evidence} >= {
        "service",
        "environment",
        "exception_type",
        "occurred_at",
        "message",
    }
    assert "Root cause" in draft.unknowns
    assert draft.next_steps


def test_invalid_citation_rejected():
    incident = event()
    payload = LocalDraftProvider().generate(incident, fingerprint(incident)).model_dump()
    payload["observations"][0]["evidence_ids"] = ["missing"]
    with pytest.raises(ValidationError, match="unavailable evidence"):
        BugDraft.model_validate(payload)


def test_legacy_drafts_still_readable():
    payload = {
        "fingerprint": "old-key",
        "title": "Legacy draft",
        "summary": "See E1.",
        "evidence": [{"id": "E1", "field": "message", "excerpt": "Timeout"}],
        "hypotheses": [],
        "reproduction": [],
    }
    assert BugDraft.model_validate(payload).observations == []


def test_database_deduplicates_durations_but_separates_http_errors(tmp_path):
    sdk = DevSwarm(tmp_path / "fingerprints.db")
    first = sdk.ingest(event(message="Upstream HTTP 401 after 3000 ms"))
    repeated = sdk.ingest(event(message="Upstream HTTP 401 after 9000 ms"))
    other = sdk.ingest(event(message="Upstream HTTP 503 after 3000 ms"))
    assert repeated.fingerprint == first.fingerprint and repeated.occurrences == 2
    assert other.fingerprint != first.fingerprint and other.occurrences == 1
