# Verification report

Prepared locally October 19-20, 2026 (America/Chicago). No remote repository was created,
no GitHub writes were performed, and no Azure resources were deployed.

## Passed

- Python 3.12: **66 tests passed** (pytest 9.1.1).
- API accept -> pending -> worker -> evidence-backed draft -> duplicate receipt.
- Concurrent intake counts 20 occurrences without duplicate rows.
- Defensive redaction occurs before storage and drafting.
- Schema rejection returns generic validation responses.
- Provider failures record bounded retry state without draft creation; fabricated evidence is rejected.
- Azure Functions HTTP handler invoked directly and via a real Core Tools 4.16.0 host.
- Azurite readiness, Functions HTTP intake, duplicate counts, generic 422 rejection,
  separate worker draft generation, shared API reads, Functions restart persistence,
  and synthetic-secret absence in database/drafts/logs all passed.
- Operational-log allowlist regression test passed. See [smoke result](local-functions-smoke.json).
- Both FastMCP servers exercised through an in-memory MCP client/tool call.
- Ruff check and formatting.
- Docker Compose configuration validation.
- Terraform 1.9.8 init (backend disabled), fmt check and validate using AzureRM 4.81.0.

## Limits

Docker daemon is stopped, so image build and container runtime checks were not performed locally.
CI includes image build. Azure deployment has not been run. Local Functions host is verified.
A dependency deprecation warning reports that Starlette's HTTPX test-client compatibility
will move to httpx2; it does not fail tests. Tested dependency versions are recorded in
requirements.lock.txt; Windows-only packages use platform markers.

The sandbox blocked default pytest temporary files and local threading; the final suite ran
outside the sandbox against synthetic telemetry in the workspace's ignored .data directory.

## Repository availability

Connected GitHub login: `rishiparpyaninortheastern`.
`get_repo(rishiparpyaninortheastern/devswarm)` returned GitHub 404 Not Found.
The authenticated owned-repository listing (including private repositories) returned no devswarm.
The name appears available at check time, but is not reserved; connector scope can affect visibility.
Recheck immediately before repository creation after user approval.

## Reference implementations

- FastMCP server running: https://github.com/PrefectHQ/fastmcp/blob/main/docs/deployment/running-server.mdx
- AzureRM Container Apps environment: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/container_app_environment
- Apache license text: https://www.apache.org/licenses/LICENSE-2.0.txt

## Installable-package verification

Wheel and source distribution pass Twine checks. The base wheel passes isolated installation
and CLI smoke tests outside the checkout. The wheel with API/Azure extras also passes real Core Tools
and Azurite testing using a CLI-generated Functions host. See [packaging](packaging.md).

Final Azure-readiness review adds prefix/subscription validation and synchronizes the packaged
Terraform template; configuration validates without a cloud plan/apply. Docker context excludes
local settings, environment files, data/logs and Terraform caches/state. See [morning review](morning-review.md).
