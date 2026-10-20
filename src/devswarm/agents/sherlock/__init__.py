from devswarm.shared.contracts import Evidence, Incident


def collect(incident: Incident) -> list[Evidence]:
    evidence = [Evidence(id="E1", field="message", excerpt=incident.message)]
    evidence += [
        Evidence(id=f"E{i + 2}", field=f"stack[{i}]", excerpt=line)
        for i, line in enumerate(incident.stack)
    ]
    return evidence
