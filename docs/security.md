# Security and trust boundaries

Only submit already-sanitized telemetry. `sanitized: true` is a producer assertion, not proof.
Strict allowlisted fields reject request bodies, arbitrary metadata and unknown fields.
The sanitization assertion must be the literal JSON boolean true; numeric lookalikes are rejected.
SDK/model instances are revalidated at the intake boundary, including instances built without validation. Defensive
redaction removes common quoted/unquoted key/value and JSON-style credentials, Bearer/Basic
authorization values, Azure AccountKey/SharedAccessKey fields, email addresses, IPv4 and URLs
before fingerprinting, persistence or draft generation. Input stack entries over 1000 characters
are rejected rather than silently truncated. Redaction occurs before enforcing output excerpt limits
(4000 characters for the message, 1000 per stack line), since replacement markers may expand text.
This is best effort, not comprehensive DLP: arbitrary secrets, names, IPv6 and unusual credentials
may remain. Producers must sanitize upstream and avoid sensitive data in service/type labels.
Validation errors return generic text, never echo raw input. The app does not log telemetry. Allowlisted operational events contain only fingerprint,
occurrence count, duplicate flag and state; no message, stack, credentials or provider exception text.

Telemetry is untrusted data. The deterministic provider never interprets it as instructions;
future LLM adapters must preserve that boundary, validate output and evidence citations, and have
no execution or publication privileges. Drafts are unverified and require human review.
No GitHub token, SDK or write operation is included. Forge remains disabled.

Local API has no authentication and must bind to loopback. Compose publishes only loopback.
MCP runs locally over stdio. SQLite is plaintext: protect host permissions, keep `.data` out of source
control, and delete local data/volumes when no longer needed. Do not submit production secrets.
Per-field limits exist, but edge-level body-size limits, authentication, quotas and retention enforcement
are required before exposing ingestion to remote clients. No such production exposure is provided.
Functions uses function-level authentication in Azure; local Core Tools may bypass it.
Azure foundation is not a hardened production deployment; see infrastructure gaps in the README.

Report vulnerabilities privately to the repository owner; do not put secrets in public issues.

Structured observations are checked for missing/duplicate evidence references. Such structural
validation does not prove the truth of an arbitrary provider's prose; the shipped deterministic
provider only describes submitted observations and keeps causal claims explicitly unknown.

Provider exception text is never persisted in retry metadata or printed by CLI processing commands.
Errors are classified as invalid_incident, provider_failed or invalid_draft; the retry budget is bounded.
Corrupt SQLite files produce a generic CLI database error rather than an unhandled traceback.
