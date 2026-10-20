# DevSwarm morning review

Prepared October 20, 2026. Overnight work is complete and saved in local Git commits on `main`.
Nothing has been created/pushed to GitHub, uploaded to PyPI/TestPyPI, or deployed to Azure.

## Start here: a two-minute review

From the `devswarm` repository directory, use the existing environment on this machine:

```powershell
.\.venv\Scripts\devswarm.exe --db .data\morning-review.db demo
```

You should see `draft_ready`, exact evidence excerpts, cited observations, explicit unknowns,
review next steps and `needs_human_review`. Run it again: the same fingerprint's occurrence count
increments. Copy its fingerprint to inspect or export:

```powershell
.\.venv\Scripts\devswarm.exe --db .data\morning-review.db show FINGERPRINT
.\.venv\Scripts\devswarm.exe --db .data\morning-review.db export FINGERPRINT
```

For a fresh installation rather than the working environment, install the wheel in a new Python
environment and use `devswarm demo`. See [package instructions](../PACKAGE_README.md).
The prepared artifacts are `dist/devswarm-0.1.0-py3-none-any.whl`, `dist/devswarm-0.1.0.tar.gz`,
and the workspace-level `devswarm-prepared.zip` source archive.

## What works

- Namespaced Python package, offline SDK/CLI, optional API/Azure/MCP extras and packaged setup templates.
- API or Azure Functions intake -> defensive sanitization -> fingerprint/deduplication -> local worker
  -> structured evidence-backed draft -> human review/JSON export. No GitHub write client exists.
- Strict boolean sanitization assertion, bounded fields, revalidated SDK inputs and improved quoted/JSON,
  Basic/Bearer and Azure-key redaction. This remains best-effort redaction, not comprehensive DLP.
- Fingerprint v2 keeps HTTP/error codes, ports and business values separate while normalizing known
  volatile values. See [synthetic HTTP scenario](../examples/http-failures.json).
- Durable attempt/error/backoff state; three-attempt failure isolation; explicit `retry FINGERPRINT`.
  One failing incident cannot indefinitely block newer healthy work. Provider exception text is suppressed.
- [Synthetic draft example](../examples/bug-draft.json), architecture/security docs, Terraform foundation,
  Docker Compose and CI definitions, with no automatic publication/deployment.

## Verification evidence

**66 tests pass** on Python 3.12 / Windows. They cover concurrent dedupe, safe intake/storage/logging,
SDK and CLI workflows, citation integrity, legacy drafts/database migration, failure isolation/backoff,
explicit recovery, Functions handler and MCP protocol calls.

The built base wheel passes an isolated installation and CLI smoke test outside the checkout.
The wheel with API/Azure extras also passes a **real Core Tools + Azurite host test**, including
HTTP 202 intake, duplicate counts, generic 422 rejection, worker drafting, API retrieval, host restart
persistence and checks that synthetic secrets are absent from data/drafts/logs. All temporary services stop.
[Latest Functions result](local-functions-smoke.json) and [repeat instructions](local-functions.md).

Ruff check/format, distribution metadata (Twine), Compose configuration and Terraform validation pass.
[Full verification report](verification.md).

## Limits to review before public use

- Alpha package, not published. Names appeared available during the initial GitHub/PyPI checks;
  availability is not reserved and must be rechecked immediately before publication.
- Docker engine is stopped: no local image build/container runtime check. CI definitions exist but
  have not run on GitHub. A Starlette/HTTPX test-client deprecation warning remains non-failing.
- Azure infrastructure is a **foundation scaffold**, not a deployed cloud application. Cloud queue,
  durable database and LLM adapters, app hosting, authentication, scoped RBAC and private networking
  are future work. [Azure readiness matrix](azure-readiness.md).
- SQLite is local/plaintext; API development mode lacks authentication; submit sanitized data only.
  Forge is disabled; Courier only exports JSON; root cause/reproduction/severity remain unverified.
- Fingerprint v2 intentionally changes earlier alpha keys. Existing records remain readable, but new
  events do not deduplicate against legacy keys. No automatic fingerprint migration is provided.

## Local commits and decisions

Run `git log --oneline` to inspect checkpoints. The first four are:

- `99a6d87`: initial offline MVP and installable package.
- `93f6d04`: credential redaction and strict incident validation.
- `3eb7bc2`: semantic fingerprints and cited draft observations.
- `26aa4a8`: bounded durable retries, failure isolation and safe CLI errors.

The final review checkpoint adds Azure-readiness documentation and safer Docker build exclusions.
No remote is configured. Test data, raw logs, virtual environments, provider caches/state and build
outputs are excluded from commits. Artifact files are kept locally for review.

## Publication decision still needed

GitHub: approve creating `rishiparpyaninortheastern/devswarm` as a public Apache-2.0 repository and
pushing the reviewed local history. PyPI/TestPyPI: separately approve release of `devswarm` 0.1.0
under the intended account after name/ownership and release verification. Neither approval has
been assumed. No cloud deployment is included in either publication decision.
