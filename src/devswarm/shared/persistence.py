"""Transactional local persistence with bounded, observable draft retries."""

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Protocol

from devswarm.agents.scribe import write
from devswarm.agents.sherlock import collect
from devswarm.shared.contracts import BugDraft, Incident, Receipt
from devswarm.shared.llm import DraftProvider
from devswarm.shared.observability import record

MAX_ATTEMPTS = 3


class DraftProcessingError(RuntimeError):
    """Safe processing failure; details and retry state are available in the local receipt."""


class IncidentStore(Protocol):
    def accept(self, key: str, incident: Incident) -> Receipt: ...
    def process_next(self, provider: DraftProvider) -> bool: ...
    def get(self, key: str) -> dict | None: ...
    def retry(self, key: str) -> bool: ...


def state(draft, attempts):
    return "draft_ready" if draft else "failed" if attempts >= MAX_ATTEMPTS else "pending"


class SQLiteStore:
    def __init__(
        self, path: str, *, clock: Callable[[], float] = time.time, retry_base_seconds: float = 1
    ):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.clock = clock
        self.retry_base_seconds = retry_base_seconds
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE IF NOT EXISTS incidents (
                fingerprint TEXT PRIMARY KEY, payload TEXT NOT NULL,
                occurrences INTEGER NOT NULL, draft TEXT)""")
            # Additive migration preserves existing incidents and already-generated drafts.
            columns = {row[1] for row in db.execute("PRAGMA table_info(incidents)")}
            for name, definition in {
                "attempts": "INTEGER NOT NULL DEFAULT 0",
                "last_error_code": "TEXT",
                "next_attempt_at": "REAL NOT NULL DEFAULT 0",
            }.items():
                if name not in columns:
                    db.execute(f"ALTER TABLE incidents ADD COLUMN {name} {definition}")

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
                """INSERT INTO incidents (fingerprint,payload,occurrences,draft) VALUES (?, ?, 1, NULL)
                ON CONFLICT(fingerprint) DO UPDATE SET occurrences=occurrences+1""",
                (key, incident.model_dump_json()),
            )
            count, draft, attempts = db.execute(
                "SELECT occurrences,draft,attempts FROM incidents WHERE fingerprint=?", (key,)
            ).fetchone()
        return Receipt(
            fingerprint=key, occurrences=count, duplicate=count > 1, state=state(draft, attempts)
        )

    def process_next(self, provider: DraftProvider) -> bool:
        # The small offline MVP serializes generation in a transaction. A crash rolls back;
        # a handled failure is committed as bounded retry state so one bad row cannot starve others.
        failed = False
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                """SELECT fingerprint,payload,attempts FROM incidents
                   WHERE draft IS NULL AND attempts < ? AND next_attempt_at <= ?
                   ORDER BY rowid LIMIT 1""",
                (MAX_ATTEMPTS, self.clock()),
            ).fetchone()
            if not row:
                return False
            key, payload, prior_attempts = row
            attempts = prior_attempts + 1
            phase = "invalid_incident"
            try:
                incident = Incident.model_validate_json(payload)
                phase = "provider_failed"
                draft = write(provider, incident, key)
                phase = "invalid_draft"
                draft = BugDraft.model_validate(draft)
                if draft.fingerprint != key or draft.evidence != collect(incident):
                    raise ValueError("Provider result did not match stored evidence")
            except Exception:  # noqa: BLE001 - isolate provider failures without storing their text
                failed = True
                db.execute(
                    """UPDATE incidents SET attempts=?,last_error_code=?,next_attempt_at=?
                       WHERE fingerprint=?""",
                    (
                        attempts,
                        phase,
                        self.clock() + self.retry_base_seconds * 2**prior_attempts,
                        key,
                    ),
                )
            else:
                db.execute(
                    """UPDATE incidents SET draft=?,attempts=?,last_error_code=NULL,next_attempt_at=0
                       WHERE fingerprint=?""",
                    (draft.model_dump_json(), attempts, key),
                )
        if failed:
            record("draft.failed", fingerprint=key, state=state(None, attempts))
            raise DraftProcessingError(
                "Draft processing failed; inspect local retry state"
            ) from None
        record("draft.created", fingerprint=key, state="needs_human_review")
        return True

    def retry(self, key: str) -> bool:
        with self.connect() as db:
            cursor = db.execute(
                """UPDATE incidents SET attempts=0,last_error_code=NULL,next_attempt_at=0
                   WHERE fingerprint=? AND draft IS NULL""",
                (key,),
            )
        return cursor.rowcount == 1

    def get(self, key: str) -> dict | None:
        with self.connect() as db:
            row = db.execute(
                """SELECT occurrences,draft,attempts,last_error_code,next_attempt_at
                   FROM incidents WHERE fingerprint=?""",
                (key,),
            ).fetchone()
        if not row:
            return None
        return {
            "fingerprint": key,
            "occurrences": row[0],
            "state": state(row[1], row[2]),
            "draft": BugDraft.model_validate_json(row[1]).model_dump() if row[1] else None,
            "processing": {
                "attempts": row[2],
                "max_attempts": MAX_ATTEMPTS,
                "last_error_code": row[3],
                "next_attempt_at": row[4] if row[1] is None and row[2] < MAX_ATTEMPTS else None,
            },
        }
