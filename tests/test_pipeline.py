import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from devswarm.agents.atlas import accept
from devswarm.agents.guardian import sanitize
from devswarm.agents.sentinel import fingerprint
from devswarm.apps.api.main import app
from devswarm.apps.worker.main import tick
from devswarm.shared.contracts import Incident
from devswarm.shared.llm import LocalDraftProvider
from devswarm.shared.persistence import DraftProcessingError, SQLiteStore


@pytest.fixture
def event():
    return Incident.model_validate(json.loads(open("examples/incident.json").read()))


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSWARM_DB", str(tmp_path / "test.db"))
    return TestClient(app)


def test_end_to_end(client, event):
    response = client.post("/incidents", json=event.model_dump(mode="json"))
    assert response.status_code == 202
    key = response.json()["fingerprint"]
    assert client.get(f"/incidents/{key}").json()["state"] == "pending"
    assert tick()
    result = client.get(f"/incidents/{key}").json()
    assert result["draft"]["evidence"][0]["excerpt"] == event.message
    assert result["draft"]["status"] == "needs_human_review"
    assert "E1" in result["draft"]["summary"]
    duplicate = client.post("/incidents", json=event.model_dump(mode="json")).json()
    assert duplicate["duplicate"] and duplicate["occurrences"] == 2
    assert not tick()


def test_redaction_before_storage(tmp_path, event):
    event.message = "token=secret123 password=p4ss email=a@example.com Authorization: Bearer abc"
    db = SQLiteStore(str(tmp_path / "redact.db"))
    key = accept(db, event).fingerprint
    db.process_next(LocalDraftProvider())
    result = json.dumps(db.get(key))
    for secret in ["secret123", "p4ss", "a@example.com", "Bearer abc"]:
        assert secret not in result
    raw = (tmp_path / "redact.db").read_bytes()
    assert b"secret123" not in raw


def test_fingerprint(event):
    first = fingerprint(sanitize(event))
    assert (
        fingerprint(event.model_copy(update={"message": event.message.replace("3000", "5000")}))
        == first
    )
    assert fingerprint(event.model_copy(update={"environment": "prod"})) != first
    assert fingerprint(event.model_copy(update={"message": "Database disconnected"})) != first


def test_concurrent_dedupe(tmp_path, event):
    db = SQLiteStore(str(tmp_path / "concurrent.db"))
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: accept(db, event), range(20)))
    assert sorted(r.occurrences for r in results) == list(range(1, 21))
    assert db.get(results[0].fingerprint)["occurrences"] == 20


def test_provider_failure_retries(tmp_path, event):
    class Broken:
        def generate(self, *args):
            raise RuntimeError("failure")

    db = SQLiteStore(str(tmp_path / "retry.db"), retry_base_seconds=0)
    key = accept(db, event).fingerprint
    with pytest.raises(RuntimeError):
        db.process_next(Broken())
    assert db.get(key)["state"] == "pending"
    assert db.process_next(LocalDraftProvider())


@pytest.mark.parametrize(
    "patch",
    [
        {"sanitized": False},
        {"extra": "secret"},
        {"service": ""},
        {"occurred_at": "2026-10-19"},
        {"stack": ["x"] * 31},
    ],
)
def test_validation(client, event, patch):
    payload = event.model_dump(mode="json") | patch
    response = client.post("/incidents", json=payload)
    assert response.status_code == 422
    assert "secret" not in response.text


def test_missing(client):
    assert client.get("/incidents/unknown").status_code == 404


def test_functions(event, tmp_path, monkeypatch):
    import azure.functions as func

    from devswarm.apps.ingestion.function_app import incidents

    monkeypatch.setenv("DEVSWARM_DB", str(tmp_path / "functions.db"))
    request = func.HttpRequest(
        method="POST", url="http://localhost/api/incidents", body=event.model_dump_json().encode()
    )
    assert incidents(request).status_code == 202


def test_mcp_preview(event):
    from devswarm.tool_servers.drafts import preview_draft

    draft = preview_draft(event)
    assert draft["status"] == "needs_human_review"


def test_no_publication():
    from devswarm.agents.forge import ENABLED

    assert not ENABLED


def test_unbacked_evidence_rejected(tmp_path, event):
    class Fabricated(LocalDraftProvider):
        def generate(self, incident, key):
            draft = super().generate(incident, key)
            draft.evidence[0].excerpt = "invented observation"
            return draft

    db = SQLiteStore(str(tmp_path / "unbacked.db"))
    key = accept(db, event).fingerprint
    with pytest.raises(DraftProcessingError):
        db.process_next(Fabricated())
    assert db.get(key)["state"] == "pending"


def test_mcp_protocol(event, tmp_path, monkeypatch):
    import asyncio

    from fastmcp import Client

    from devswarm.tool_servers.drafts import mcp as drafts
    from devswarm.tool_servers.evidence import mcp as evidence

    monkeypatch.setenv("DEVSWARM_DB", str(tmp_path / "mcp.db"))

    async def exercise():
        async with Client(drafts) as client:
            tools = await client.list_tools()
            assert [tool.name for tool in tools] == ["preview_draft"]
            result = await client.call_tool(
                "preview_draft", {"incident": event.model_dump(mode="json")}
            )
            assert not result.is_error
            assert "needs_human_review" in str(result)
        async with Client(evidence) as client:
            result = await client.call_tool("get_incident", {"fingerprint": "missing"})
            assert not result.is_error
            assert "not_found" in str(result)

    asyncio.run(exercise())


def test_operational_logs_are_safe(event, tmp_path, caplog):
    import logging

    from devswarm.shared.observability import record

    event.message = "token=synthetic-secret user@example.com"
    with caplog.at_level(logging.INFO, logger="devswarm.operations"):
        db = SQLiteStore(str(tmp_path / "logs.db"))
        accept(db, event)
        db.process_next(LocalDraftProvider())
        record("example", message="synthetic-secret")
    assert "incident.accepted" in caplog.text
    assert "draft.created" in caplog.text
    assert "synthetic-secret" not in caplog.text
    assert "user@example.com" not in caplog.text
