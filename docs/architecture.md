# Architecture

The previous conversation's assistant architecture was unavailable (reference placeholders).
This scaffold follows the paths and requirements in the current request; the role assignments below
are explicit implementation choices.

```mermaid
flowchart LR
  Input[Sanitized incident] --> API[API or Functions]
  API --> Guardian[Guardian: defensive redaction]
  Guardian --> Sentinel[Sentinel: stable fingerprint]
  Sentinel --> DB[(SQLite: incident + pending work)]
  DB --> Atlas[Atlas / worker orchestration]
  Atlas --> Sherlock[Sherlock: evidence]
  Sherlock --> Scribe[Scribe: local structured draft]
  Scribe --> DB
  DB --> Human[Human review / Courier export]
```

Atlas coordinates intake. Sentinel hashes service, environment, exception, normalized message and
stack; timestamps are excluded and numbers/UUIDs are normalized. Distinct messages and environments
remain separate. This heuristic can merge distinct numeric errors or split text variants; review is required.
SQLite uses unique keys and immediate transactions so simultaneous repeats increment exactly once per request.
Delivery is at least once: there is no producer event ID, so transport retries count as occurrences.
A crash during drafting rolls back and the next poll retries. Single-transaction local drafting intentionally
serializes workers; it is suitable for a small offline MVP, not slow remote inference.
Only the first sanitized observation is retained per fingerprint; counts include repeats.
Drafts cite exact message/stack excerpts, label root cause and reproduction unknown, and require human review.

Scribe's DraftProvider protocol supports future Azure-hosted LLM adapters; only deterministic local
inference is implemented. IncidentStore defines the persistence seam. Forge is disabled; Guardian
sanitizes inputs; Courier exports JSON without network access. Two FastMCP servers expose only
read/preview operations. No agent can execute telemetry as code or publish a GitHub issue/PR.

## Azure target and staged implementation

Target: Functions ingestion -> Service Bus -> Container Apps worker/API -> durable database/blob evidence,
with managed identities, Entra ID, Key Vault, Monitor and an optional Azure-hosted model.
Terraform currently supplies only the foundation described in its README. Cloud database, queue and
LLM adapters, hosting resources, permissions and deployment pipeline are intentionally unimplemented.
SQLite must not be shared across independently scaled cloud replicas. Do not deploy this local API publicly.

## Package layout

Installable code lives exclusively under `src/devswarm`, including apps, agents, shared modules
and MCP servers. Root apps retain host wrappers; root agent directories point to their packaged
implementations. Pydantic is the base dependency; API, MCP and Functions are optional extras.
The CLI exports local Functions and Terraform templates without provisioning anything.
