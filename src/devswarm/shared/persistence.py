import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol

from devswarm.agents.scribe import write
from devswarm.agents.sherlock import collect
from devswarm.shared.contracts import BugDraft, Incident, Receipt
from devswarm.shared.llm import DraftProvider
from devswarm.shared.observability import record


class IncidentStore(Protocol):
    def accept(self, key: str, incident: Incident) -> Receipt: ...
    def process_next(self, provider: DraftProvider) -> bool: ...
    def get(self, key: str) -> dict | None: ...


class SQLiteStore:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS incidents (
                fingerprint TEXT PRIMARY KEY, payload TEXT NOT NULL,
                occurrences INTEGER NOT NULL, draft TEXT)""")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    def accept(self, key: str, incident: Incident) -> Receipt:
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """INSERT INTO incidents VALUES (?, ?, 1, NULL)
                ON CONFLICT(fingerprint) DO UPDATE SET occurrences=occurrences+1""",
                (key, incident.model_dump_json()),
            )
            count, draft = db.execute(
                "SELECT occurrences,draft FROM incidents WHERE fingerprint=?", (key,)
            ).fetchone()
        return Receipt(
            fingerprint=key,
            occurrences=count,
            duplicate=count > 1,
            state="draft_ready" if draft else "pending",
        )

    def process_next(self, provider: DraftProvider) -> bool:
        # One local transaction prevents competing workers from generating the same draft.
        # Exceptions roll back; the pending item can be retried on the next poll.
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT fingerprint,payload FROM incidents WHERE draft IS NULL LIMIT 1"
            ).fetchone()
            if not row:
                return False
            key, payload = row
            incident = Incident.model_validate_json(payload)
            draft = write(provider, incident, key)
            draft = BugDraft.model_validate(draft)
            if draft.fingerprint != key:
                raise ValueError("Provider returned a mismatched fingerprint")
            if draft.evidence != collect(incident):
                raise ValueError("Provider evidence must match the stored observation")
            db.execute(
                "UPDATE incidents SET draft=? WHERE fingerprint=?", (draft.model_dump_json(), key)
            )
        record("draft.created", fingerprint=key, state="needs_human_review")
        return True

    def get(self, key: str) -> dict | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT occurrences,draft FROM incidents WHERE fingerprint=?", (key,)
            ).fetchone()
        if not row:
            return None
        return {
            "fingerprint": key,
            "occurrences": row[0],
            "state": "draft_ready" if row[1] else "pending",
            "draft": BugDraft.model_validate_json(row[1]).model_dump() if row[1] else None,
        }
