"""Stable offline entry point for Python consumers."""

from pathlib import Path

from devswarm.agents.atlas import accept
from devswarm.shared.contracts import Incident, Receipt
from devswarm.shared.llm import DraftProvider, LocalDraftProvider
from devswarm.shared.persistence import SQLiteStore


class DevSwarm:
    def __init__(
        self, database: str | Path = ".data/devswarm.db", provider: DraftProvider | None = None
    ):
        self.store = SQLiteStore(str(database))
        self.provider = provider or LocalDraftProvider()

    def ingest(self, incident: Incident | dict) -> Receipt:
        return accept(self.store, Incident.model_validate(incident))

    def process_next(self) -> bool:
        return self.store.process_next(self.provider)

    def get(self, fingerprint: str) -> dict | None:
        return self.store.get(fingerprint)

    def retry(self, fingerprint: str) -> bool:
        """Reset local pending/failed work for an explicit retry; completed drafts are preserved."""
        return self.store.retry(fingerprint)
