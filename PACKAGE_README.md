# DevSwarm

Local-first, evidence-backed incident triage. Apache 2.0 licensed, alpha release.
Accept sanitized telemetry, fingerprint/deduplicate it, and generate a structured bug draft
with exact evidence excerpts and explicit unknowns. No model key or cloud account required.
No automatic GitHub writes or code execution.

## Installation

**This release is prepared locally and has not been published to PyPI.** Install the supplied wheel:

```sh
python -m pip install ./devswarm-0.1.0-py3-none-any.whl
```

After an approved PyPI release, the intended public command is `pip install devswarm`.
Use Python 3.11+. The base package requires Pydantic; optional integrations are separate:

```sh
# After publication, or use the matching wheel path with extras before publication:
pip install 'devswarm[api]'    # FastAPI + Uvicorn
pip install 'devswarm[mcp]'    # FastMCP tool servers
pip install 'devswarm[azure]'  # Azure Functions entry point
pip install 'devswarm[all]'    # All optional integrations
```

## Offline quick start

```sh
devswarm --db ./incidents.db demo
devswarm sample > incident.json
devswarm --db ./incidents.db ingest incident.json
devswarm --db ./incidents.db worker --once
devswarm --db ./incidents.db show FINGERPRINT
devswarm --db ./incidents.db export FINGERPRINT
```

`demo` uses a bundled fixture, stores it locally and creates a reviewable draft. Repeated intake
increments its occurrence count. The fingerprint is returned by `ingest` and `demo`.
`python -m devswarm` supports the same commands. `DEVSWARM_DB` sets the database default;
`--db` overrides it. The fallback is `.data/devswarm.db` in the current working directory.
Operational events go to stderr; command results are JSON on stdout.

## Python API

```python
from devswarm import DevSwarm, Incident

swarm = DevSwarm("./incidents.db")
incident = Incident(
    service="checkout",
    environment="local",
    exception_type="TimeoutError",
    message="Inventory request timed out",
    stack=["checkout.py:42 in reserve_inventory"],
    occurred_at="2026-10-19T18:00:00Z",
    sanitized=True,
)
receipt = swarm.ingest(incident)
swarm.process_next()
result = swarm.get(receipt.fingerprint)
print(result["draft"])
```

## Optional integrations

With the corresponding extra installed:

```sh
devswarm --db ./incidents.db serve --port 8000
devswarm --db ./incidents.db worker --watch
devswarm --db ./incidents.db mcp evidence
devswarm mcp drafts
devswarm --db ./incidents.db init-functions ./functions-host
devswarm init-azure ./azure-foundation
```

The API binds to loopback. MCP uses stdio. `init-functions` creates host files for Core Tools;
install Core Tools and Azurite separately, activate the same Python environment, start Azurite,
then run `func start` in the generated host directory. `init-azure` exports a Terraform foundation;
it does not provision resources or provide cloud database/queue adapters. Initializers refuse
to overwrite existing files. Docker, Terraform, Core Tools and Azurite are external tools,
not binaries bundled into the Python package.

## Security and limitations

Submit only upstream-sanitized telemetry. Defensive redaction is best effort, not comprehensive DLP.
SQLite is plaintext and intended for local use. Root cause and exact reproduction remain unverified;
drafts require human review. Numeric/UUID normalization is heuristic. Forge is disabled and Courier
exports JSON only. This alpha has no production authentication or hosted Azure deployment.
