from typing import Protocol

from devswarm.agents.sherlock import collect
from devswarm.shared.contracts import BugDraft, Incident


class DraftProvider(Protocol):
    def generate(self, incident: Incident, fingerprint: str) -> BugDraft: ...


class LocalDraftProvider:
    def generate(self, incident: Incident, fingerprint: str) -> BugDraft:
        return BugDraft(
            fingerprint=fingerprint,
            title=f"{incident.service}: {incident.exception_type}",
            summary=f"Observed {incident.exception_type} in {incident.environment}; see E1.",
            evidence=collect(incident),
            hypotheses=["Root cause is unverified; inspect the cited stack and source."],
            reproduction=[
                "Exact reproduction is unknown.",
                "Use the sanitized evidence to prepare a reproduction in an isolated environment.",
            ],
        )
