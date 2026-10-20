# DevSwarm overnight plan

Status: completed early; see `morning-review.md`. Publication remains pending human approval.

Review target: October 20, 2026, 8:00 a.m. America/Chicago.

## Objective
Turn the prepared local-first incident-to-bug-draft scaffold into a reliable, reviewable MVP.
Preserve the public Apache-2.0 publication proposal, but do not create the GitHub repository,
push code, publish issues/PRs, deploy cloud resources, or incur paid service usage.
All files under the project sources directory remain read-only.

## Work sequence

1. **Audit and prioritize.** Inspect the current implementation and all requested paths. Record actual defects,
   missing requirements, and tradeoffs. Fix high-value correctness issues before expanding scope.
2. **Harden intake and persistence.** Review validation limits, secret redaction, fingerprint collisions,
   repeat delivery semantics, concurrency, worker rollback/retry, and evidence integrity. Add meaningful
   regression tests for defects found. Keep local SQLite semantics explicit.
3. **Improve draft usefulness.** Add realistic sanitized fixtures and structured observed/unknown information.
   Make every factual draft claim traceable to evidence. Retain deterministic offline operation.
   Keep Forge disabled and Courier limited to local export.
4. **Verify integration and developer experience.** Exercise API, Functions handler, background worker,
   MCP protocol, restart persistence and export. Improve quick-start reliability, CI, portable dependency
   constraints, and demo commands. Run Docker checks if the engine becomes available; otherwise document
   the exact unverified parts without claiming success.
5. **Review Azure readiness.** Align documentation and Terraform with the intended Functions, Service Bus,
   Container Apps and durable-storage architecture. Improve scaffold interfaces and validation where useful,
   while marking unimplemented cloud adapters and deployment requirements clearly. No terraform apply.
6. **Morning handoff.** Produce docs/morning-review.md with a short walkthrough, implemented changes,
   verification evidence, known gaps, architecture decisions, and the exact publication approval still needed.
   Refresh the prepared source archive, excluding environments, telemetry, secrets and caches.

## Completion criteria

- A fresh user can follow the documented local setup and submit a fixture, generate a draft,
  inspect evidence, re-submit it and see deduplication, and export for human review.
- Relevant regression and integration tests pass; lint/format, Compose and Terraform validations pass.
- Failures remain visible and retryable, telemetry is handled as untrusted data, and no GitHub write path exists.
- Documentation distinguishes tested behavior, mocked adapters, infrastructure scaffold, and unverified claims.
- Morning review pack is ready with no remote publication or deployment.

## Overnight cadence

Continue this chat's authorized local work in hourly follow-up runs until the morning deadline.
Each run reads this plan and docs/overnight-progress.md, advances the next useful unfinished milestone,
and records concise progress and verification results. Avoid duplicate changes and repetitive tests.
Notify only on completion, a meaningful failure, or required user action. If finished early, stop making
changes and prepare the review pack. If blocked, finish independent work and document the blocker.

## Additional local-test authorization

The user explicitly permits autonomous local Azure Functions testing, creating synthetic logs,
reading logs, installing local tools and running local emulators. Include a real Core Tools host
and Azurite smoke test and inspect logs for accidental secret disclosure.

## Installable package milestone

The user additionally requested a public-use pip package. Package code under one devswarm namespace,
provide an offline SDK/CLI and optional API/Azure/MCP extras, build wheel + source distribution,
verify a fresh installation outside the checkout and generated Functions-host startup, and document
release steps. Keep PyPI and TestPyPI uploads pending explicit approval, alongside GitHub publication.
Preserve this packaging capability and smoke coverage during all subsequent overnight changes.

## Local commit cadence

The user authorizes ongoing local Git commits. Commit each completed, verified milestone with
a concise message. Inspect staged changes and exclude telemetry, environments, logs, secrets,
Terraform caches/state and build outputs. Do not create empty commits or push/create a remote.
GitHub and PyPI publication still require explicit approval.
