# Real local Azure Functions verification

Verified with Python 3.12, Azure Functions Core Tools 4.16.0 / runtime 4.1054.250.26428,
and the npm Azurite emulator on Windows. No Azure account or cloud resources are used.

## Repeatable smoke test

Install the repository in a virtual environment as described in the README. Install local tools
outside the source tree, e.g. from the parent workspace:

```powershell
npm.cmd install --prefix .tools/functions azure-functions-core-tools@4 azurite --no-audit --no-fund
```

Wait for installation to finish before running the test; the bundled Python worker is unpacked last.
From the repository root, with the virtual environment active:

```powershell
python scripts/local_functions_smoke.py --func ../.tools/functions/node_modules/azure-functions-core-tools/bin/func.exe --azurite ../.tools/functions/node_modules/azurite/dist/src/azurite.js
```

For another OS, supply the Core Tools executable via `--func`, a node executable via `--node`
if needed, and the Azurite JS entry point via `--azurite`. Windows is the platform verified here.

The script uses ports 7075 (Functions), 8075 (API) and 10000-10002 (Azurite). It refuses to
reuse occupied ports, creates a fresh ignored `.data/functions-smoke-TIMESTAMP` directory,
and starts hidden child processes that it stops in a finally block. It waits for the blob service,
Functions host and API to become ready. Only synthetic telemetry is submitted.

The test verifies first intake, duplicate intake, rejected unsanitized input, pending work,
separate worker generation, evidence redaction, API retrieval, repeat after drafting and host restart.
It checks generated service logs, the database and the returned draft for synthetic-secret leakage.
Azurite is verified as an available host-storage emulator; incident persistence still uses SQLite.
This HTTP-only function does not test Blob/Queue/Table bindings or Service Bus.

Artifacts: `functions.log`, `functions-restarted.log`, `api.log`, `worker.log`, `azurite.log`,
`azurite-debug.log`, `draft.json`, `incidents.db`, and `report.json` in that run directory.
A source-safe summary of the passing run is in [local-functions-smoke.json](local-functions-smoke.json).

## Manual host

1. Activate the repository virtual environment and start Azurite separately.
2. Copy `apps/ingestion/local.settings.example.json` to `apps/ingestion/local.settings.json`.
   The real settings file is ignored by Git. The example contains only development values.
3. Set `PYTHONPATH` to the absolute repository directory and put the virtual environment Python on PATH.
4. From `apps/ingestion`, run `func start`.
5. POST `examples/incident.json` to `http://localhost:7071/api/incidents`.
6. Run `python -m apps.worker.main --once` from the repository root; the example relative database
   setting matches the worker's default `.data/devswarm.db` when each command uses these directories.

Core Tools can bypass function-key authentication locally. Do not expose this development host
as a public service. For Azure deployment, install/package the shared repository code and use
durable cloud adapters; the current SQLite setup is local-only.

Official guidance: [Develop Azure Functions locally](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local).
