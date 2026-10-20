# Python distribution readiness

Prepared distribution: `devswarm` 0.1.0 (alpha), Apache-2.0, Python 3.11+.
PyPI's public metadata endpoint returned 404 for devswarm during this check. This suggests
availability, not a reservation or guarantee; recheck before release and choose another name if needed.
Nothing has been uploaded to PyPI or TestPyPI.

## Artifacts and supported interfaces

`dist/devswarm-0.1.0-py3-none-any.whl` is the installable wheel.
`dist/devswarm-0.1.0.tar.gz` is the source distribution with documentation, Terraform and tests.
Code is namespaced entirely under `devswarm`, avoiding generic top-level packages like `shared`.

- Base: Pydantic contracts, offline SDK, SQLite, local drafting and CLI.
- `[api]`: FastAPI/Uvicorn; `[azure]`: Functions SDK; `[mcp]`: FastMCP; `[all]`: all three.
- `DevSwarm`, `Incident`, `BugDraft`, `Receipt` are exported at the Python package root.
- `devswarm` / `python -m devswarm`: sample, demo, ingest, worker, show, export, serve,
  MCP servers, local Functions initializer and Azure Terraform scaffold exporter.
- Docker, Core Tools, Azurite and Terraform remain external tools. They are not wheel binaries.

See [package quick start](../PACKAGE_README.md). Operational metadata goes to stderr;
command JSON goes to stdout. All generated drafts require human review.

## Build and verify

```sh
pip install -e '.[dev]'
python -m build
python -m twine check dist/*
python -m venv .data/package-env
# Windows: .data/package-env/Scripts/python.exe
.data/package-env/bin/python -m pip install dist/devswarm-0.1.0-py3-none-any.whl
python scripts/installed_package_smoke.py --python .data/package-env/bin/python
```

The package smoke script requires a base-only clean environment, before installing optional extras.
It runs outside the source directory and clears PYTHONPATH. CI builds/validates distributions,
installs the base wheel into an isolated environment, runs this check and retains distribution artifacts.
CI has no publishing step or PyPI credentials.

Verified locally on Python 3.12:

- 59 regression tests pass, including SDK, CLI, safe error output, no-overwrite initialization,
  evidence integrity, concurrent deduplication, MCP calls and Functions intake.
- Wheel and source distribution pass Twine metadata checks.
- Fresh base-only wheel install runs demo, repeat, export and scaffold creation outside checkout.
- Optional API/MCP commands report the required extra when dependencies are absent.
- The wheel installs only the devswarm namespace and includes Apache license files and resource templates.
- After installing the wheel's API/Azure extras, its generated Functions host passed the full
  real Core Tools + Azurite smoke test, including worker processing and host restart persistence.

Only Python 3.12 on Windows has been executed locally. Other declared Python/OS combinations
should be verified in CI before declaring a stable release.

## Public release gate

Before any TestPyPI or PyPI upload: obtain explicit publication approval, recheck the name,
review artifact contents and license, verify the intended PyPI owner, and set up that owner's
credentials or Trusted Publishing. No account ownership or upload rights have been assumed.
Validate a TestPyPI release first if approved; then approve the final PyPI release.
Do not request or store tokens in the repository. GitHub publication is a separate pending approval.

References: [PyPA packaging tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
and [distribution guidance](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/).
