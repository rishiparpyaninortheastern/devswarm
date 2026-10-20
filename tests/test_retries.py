"""Failure isolation, retry scheduling and legacy-schema preservation regressions."""

import json
import sqlite3
from importlib.resources import files

import pytest

from devswarm import DevSwarm, Incident
from devswarm.agents.atlas import accept
from devswarm.cli import main
from devswarm.shared.llm import LocalDraftProvider
from devswarm.shared.persistence import DraftProcessingError, SQLiteStore


def incident(message="failure"):
    value = json.loads(files("devswarm.resources").joinpath("incident.json").read_text())
    return Incident.model_validate(value | {"message": message})


class SelectiveProvider(LocalDraftProvider):
    def generate(self, event, key):
        if event.message == "poison":
            raise RuntimeError("synthetic-provider-secret")
        return super().generate(event, key)


def test_failed_item_does_not_starve_healthy_work(tmp_path):
    now = [100.0]
    db = SQLiteStore(str(tmp_path / "queue.db"), clock=lambda: now[0])
    bad = accept(db, incident("poison")).fingerprint
    good = accept(db, incident("healthy")).fingerprint
    with pytest.raises(DraftProcessingError) as failure:
        db.process_next(SelectiveProvider())
    assert "synthetic-provider-secret" not in str(failure.value)
    assert db.get(bad)["processing"]["next_attempt_at"] == 101
    assert db.get(bad)["processing"]["last_error_code"] == "provider_failed"
    assert db.process_next(SelectiveProvider())
    assert db.get(good)["state"] == "draft_ready"
    assert not db.process_next(SelectiveProvider())
    for timestamp in [101, 103]:
        now[0] = timestamp
        with pytest.raises(DraftProcessingError):
            db.process_next(SelectiveProvider())
    assert db.get(bad)["state"] == "failed"
    assert db.get(bad)["processing"]["attempts"] == 3
    assert not db.process_next(SelectiveProvider())
    assert "synthetic-provider-secret" not in json.dumps(db.get(bad))
    assert b"synthetic-provider-secret" not in (tmp_path / "queue.db").read_bytes()
    assert accept(db, incident("poison")).state == "failed"
    assert db.retry(bad)
    assert db.get(bad)["processing"]["attempts"] == 0
    assert db.process_next(LocalDraftProvider())
    assert db.get(bad)["state"] == "draft_ready"
    assert not db.retry(bad)


def test_legacy_schema_migrates_without_losing_records(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TABLE incidents (fingerprint TEXT PRIMARY KEY, payload TEXT, occurrences INTEGER, draft TEXT)"
        )
        db.execute(
            "INSERT INTO incidents VALUES (?, ?, 7, NULL)",
            ("legacy-key", incident().model_dump_json()),
        )
    current = SQLiteStore(str(path))
    assert current.get("legacy-key")["occurrences"] == 7
    assert current.process_next(LocalDraftProvider())
    assert current.get("legacy-key")["state"] == "draft_ready"
    assert SQLiteStore(str(path)).get("legacy-key")["occurrences"] == 7


def test_cli_database_failure_is_safe(tmp_path, capsys):
    path = tmp_path / "bad.db"
    path.write_bytes(b"synthetic corrupt database")
    assert main(["--db", str(path), "demo"]) == 2
    output = capsys.readouterr()
    assert "local_database_error" in output.err
    assert "Traceback" not in output.err


def test_cli_processing_failure_is_safe(tmp_path, capsys, monkeypatch):
    def broken(self):
        raise DraftProcessingError("synthetic-provider-secret")

    monkeypatch.setattr(DevSwarm, "process_next", broken)
    assert main(["--db", str(tmp_path / "cli.db"), "worker", "--once"]) == 1
    output = capsys.readouterr()
    assert "draft_processing_failed" in output.err
    assert "synthetic-provider-secret" not in output.err


def test_explicit_retry_command_preserves_completed_drafts(tmp_path, capsys):
    path = str(tmp_path / "retry.db")
    sdk = DevSwarm(path)
    key = sdk.ingest(incident()).fingerprint
    assert main(["--db", path, "retry", key]) == 0
    assert json.loads(capsys.readouterr().out)["reset"]
    assert sdk.process_next()
    assert main(["--db", path, "retry", key]) == 0
    assert not json.loads(capsys.readouterr().out)["reset"]
    assert sdk.get(key)["draft"] is not None


def test_export_reports_failed_state(tmp_path, capsys):
    path = str(tmp_path / "failed.db")
    store = SQLiteStore(path, retry_base_seconds=0)
    key = accept(store, incident("poison")).fingerprint
    for _ in range(3):
        with pytest.raises(DraftProcessingError):
            store.process_next(SelectiveProvider())
    assert main(["--db", path, "export", key]) == 1
    assert "draft_failed" in capsys.readouterr().err


def test_cli_watch_continues_after_handled_failure(tmp_path, capsys, monkeypatch):
    calls = []

    def next_item(self):
        calls.append(1)
        if len(calls) == 1:
            raise DraftProcessingError("synthetic-provider-secret")
        raise KeyboardInterrupt

    monkeypatch.setattr(DevSwarm, "process_next", next_item)
    monkeypatch.setattr("devswarm.cli.time.sleep", lambda _: None)
    assert main(["--db", str(tmp_path / "watch.db"), "worker", "--watch"]) == 130
    assert len(calls) == 2
    assert "synthetic-provider-secret" not in capsys.readouterr().err
