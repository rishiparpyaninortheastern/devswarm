from devswarm.shared.contracts import BugDraft, Incident
from devswarm.shared.llm import DraftProvider


def write(provider: DraftProvider, incident: Incident, fingerprint: str) -> BugDraft:
    return provider.generate(incident, fingerprint)
