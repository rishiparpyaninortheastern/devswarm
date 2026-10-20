# Azure readiness review

This is an Azure-oriented local MVP plus a validated Terraform foundation. It is not a deployed
cloud application. No Azure account was accessed, no plan/apply was run, and no paid service was used.

| Component | Implemented and verified | Work before cloud deployment |
|---|---|---|
| HTTP ingestion | Python Functions entry point; real local Core Tools host | Hosting plan/app resources, packaging, authentication, rate/body limits |
| Storage emulator | Azurite startup/readiness in local smoke | Real host-storage account, identity/access policy, retention |
| Incident persistence | SQLite transactions, schema migration, dedupe, bounded retries | Durable shared database adapter, schema/indexes, tenant isolation |
| Queue | Local database-backed pending work | Service Bus producer/consumer adapters, transport dedupe, leases, dead-letter triage |
| Worker/API | Local Python worker and FastAPI; shared SQLite in smoke test | Container images/apps, autoscaling, health probes, separate scoped identities |
| Model provider | Deterministic offline provider behind a protocol | Approved Azure-hosted model adapter, configuration, evaluation and data policy |
| Monitoring | Safe local operational events | Cloud diagnostics, alerts, availability/SLOs, access and retention controls |
| Security | Strict contracts, best-effort redaction, local review/export only | Entra ID, private networking, Key Vault, scoped RBAC, audit and deletion policy |
| Terraform | RG, Container Apps environment, Log Analytics, Service Bus queue, managed identity | App hosting/storage/RBAC resources, private endpoints, remote state, deployment pipeline |

## Identity and duplicates

Current counts represent accepted HTTP deliveries: two transport retries count twice. When adding
Service Bus, use a stable **producer event ID** as MessageId to deduplicate redelivery of one event.
Do not use the incident fingerprint as MessageId: separate real observations can share a fingerprint
and must still increment the occurrence count. The current incident contract has no producer event ID;
adding this requires an explicit contract/transport-adapter change.

## Deployment boundaries

- Use an owned, globally unique prefix when planning the Service Bus namespace. Defaults are examples,
  not reserved names. Prefix and subscription-GUID input validation are included.
- The foundation disables Service Bus shared-key authentication, but does not grant runtime RBAC.
  Separate sender/receiver identities and narrow roles must be configured with the future adapters.
- Public-network restrictions, Key Vault, app hosting and remote-state configuration are not supplied.
  Review these before any production use. Do not scale the SQLite implementation across replicas.
- Terraform validate passed with 1.9.8 / AzureRM 4.81.0. This proves configuration/schema validity,
  not resource availability, naming availability, quotas, permissions, budget or deployment success.
- The package's exported Terraform template is synchronized with the monorepo source template.
  Docker build context now excludes local settings, environment files, data/logs and Terraform caches/state.

## What was not verified

Docker Desktop's engine remains stopped, so container image build/runtime checks could not run locally.
Compose configuration validates and CI includes image build. No GitHub-hosted CI run exists yet because
the repository is still local. Other Python versions and operating systems remain CI/release checks;
local execution used Python 3.12 on Windows.
