from typing import Protocol

from devswarm.agents.sherlock import collect
from devswarm.shared.contracts import BugDraft, Incident, Observation


class DraftProvider(Protocol):
    def generate(self, incident: Incident, fingerprint: str) -> BugDraft: ...


class LocalDraftProvider:
    def generate(self, incident: Incident, fingerprint: str) -> BugDraft:
        return BugDraft(
            fingerprint=fingerprint,
            title=f"{incident.service}: {incident.exception_type}",
            summary=f"Observed {incident.exception_type} in {incident.environment}; see E1.",
            evidence=collect(incident),
            observations=[
                Observation(
                    statement=f"Telemetry reports {incident.exception_type} for {incident.service} in {incident.environment}.",
                    evidence_ids=["C1", "C2", "C3"],
                ),
                Observation(
                    statement="The submitted event includes the failure message shown in E1.",
                    evidence_ids=["E1"],
                ),
                Observation(
                    statement=f"Producer reported the event time as {incident.occurred_at.isoformat()}.",
                    evidence_ids=["C4"],
                ),
            ],
            unknowns=[
                "Root cause",
                "Exact reproduction steps",
                "Affected source revision",
                "User impact and severity",
                "Whether the failure is still occurring",
            ],
            next_steps=[
                "Review E1 and any stack evidence against the affected source revision.",
                "Reproduce in an isolated environment before proposing a fix.",
                "Have a maintainer verify impact and approve any external issue.",
            ],
            hypotheses=["Root cause is unverified; inspect the cited stack and source."],
            reproduction=[
                "Exact reproduction is unknown.",
                "Use the sanitized evidence to prepare a reproduction in an isolated environment.",
            ],
        )
