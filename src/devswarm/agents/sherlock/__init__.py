from devswarm.shared.contracts import Evidence, Incident


def collect(incident: Incident) -> list[Evidence]:
    evidence = [Evidence(id="E1", field="message", excerpt=incident.message)]
    evidence += [
        Evidence(id=f"E{i + 2}", field=f"stack[{i}]", excerpt=line)
        for i, line in enumerate(incident.stack)
    ]
    evidence += [
        Evidence(id="C1", field="service", excerpt=incident.service),
        Evidence(id="C2", field="environment", excerpt=incident.environment),
        Evidence(id="C3", field="exception_type", excerpt=incident.exception_type),
        Evidence(id="C4", field="occurred_at", excerpt=incident.occurred_at.isoformat()),
    ]
    return evidence
