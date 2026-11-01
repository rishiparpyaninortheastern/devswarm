# DevSwarm

Start with the [morning review](docs/morning-review.md) for the demo, verified behavior and release decisions.

Apache 2.0 licensed, Azure-oriented monorepo for evidence-backed incident triage.
The working MVP is local-first: no cloud subscription, LLM key or GitHub token needed.
Telemetry becomes a reviewable structured bug draft; no issues or PRs are published.

## Install directly with pip

```sh
pip install "git+https://github.com/rishiparpyaninortheastern/devswarm.git"
devswarm demo
```

Requires Python 3.11+ and Git. Plain `pip install devswarm` is pending the first PyPI release;
see [release setup](docs/pypi-release.md). Do not assume the PyPI name has been registered yet.

## Installable Python package

A compact wheel and source distribution are prepared under `dist/`; nothing is uploaded to PyPI.
See [package quick start](PACKAGE_README.md) for the `devswarm` command, Python API and optional extras.
The implementation lives under `src/devswarm`; the `apps` directories retain monorepo host entry points.

## Quick start

Python 3.11+ (3.12 recommended), or Docker Compose:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate; macOS/Linux: source .venv/bin/activate
python -m pip install -c requirements.lock.txt -e ".[dev]"
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
# In another terminal with the same virtual environment and repository directory:
python -m apps.worker.main
```

Or run `docker compose up --build` (API + worker share a named SQLite volume).
Open http://127.0.0.1:8000/docs for interactive intake and draft retrieval.

```sh
curl -X POST http://127.0.0.1:8000/incidents -H "Content-Type: application/json" --data-binary @examples/incident.json
# Copy fingerprint from the 202 receipt:
curl http://127.0.0.1:8000/incidents/FINGERPRINT
```

PowerShell: use `curl.exe` to avoid the legacy alias. The initial state is `pending`;
within a worker poll it becomes `draft_ready`. Re-submit the sample to see occurrences increment.
For deterministic one-item processing: `python -m apps.worker.main --once`.
Set `DEVSWARM_DB` identically for each process to change `.data/devswarm.db`.
Stop services with Ctrl+C or `docker compose down`; the volume retains data.
`docker compose down -v` explicitly deletes the local database volume.

## Contents

- `apps/api`: FastAPI intake/status; `apps/ingestion`: Azure Functions HTTP entry point;
  `apps/worker`: durable pending-item polling.
- `agents/atlas`, `sentinel`, `sherlock`, `scribe`, `guardian`, `courier`, `forge`:
  orchestration, fingerprinting, evidence, drafting, sanitization, export, future patch generation.
- `shared`: strict Pydantic contracts, persistence and LLM provider protocols, local adapters.
- `tool_servers`: FastMCP evidence reader and stateless draft preview (stdio).
- `infra/terraform`: Azure foundation; `tests`, `.github/workflows`, `docs`: verification and design.

Run MCP servers from this directory: `devswarm mcp evidence` or
`devswarm mcp drafts`. Configure your MCP host with that command and working directory.
Do not expose stdio tools as unauthenticated network services.

Azure Functions Core Tools can run the ingestion host from `apps/ingestion` after installing
the repository in the active environment and setting `PYTHONPATH` to the repository root.
For a fully local host, set `AzureWebJobsStorage=UseDevelopmentStorage=true` and run Azurite.
The Functions entry point is verified through a real local host, including restart persistence.
See [local Functions test](docs/local-functions.md) for the repeatable smoke test and logs.
Hosted Azure deployment is future work.

## Verification

```sh
pytest -q
ruff check .
docker compose config --quiet
terraform -chdir=infra/terraform init -backend=false
terraform -chdir=infra/terraform validate
```

See [architecture](docs/architecture.md), [security](docs/security.md),
[verification](docs/verification.md), and [Azure foundation](infra/terraform/README.md).
Dependency ranges are in `pyproject.toml`; `requirements.lock.txt` records the tested environment.

## Publication

Prepared for `rishiparpyaninortheastern/devswarm`, public, Apache-2.0.
Published to [GitHub](https://github.com/rishiparpyaninortheastern/devswarm) with user approval.
PyPI/TestPyPI publication and Azure deployment remain separate, pending decisions.
