from devswarm.agents.guardian import sanitize
from devswarm.agents.sentinel import fingerprint
from devswarm.shared.contracts import Incident
from devswarm.shared.observability import record
from devswarm.shared.persistence import IncidentStore


def accept(store: IncidentStore, incident: Incident):
    safe = sanitize(incident)
    receipt = store.accept(fingerprint(safe), safe)
    record("incident.accepted", **receipt.model_dump())
    return receipt
