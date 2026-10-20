# Azure foundation (not a deployed application)

Run `terraform init`, `terraform fmt`, `terraform validate`, then review `terraform plan -var subscription_id=...`.
Do not apply without an explicit deployment decision. No cloud operations run in CI.

This foundation provisions a resource group, Container Apps environment, managed identity,
Log Analytics and a Service Bus queue with duplicate detection/dead lettering.
It deliberately does not deploy the SQLite application across Azure instances.
Before cloud activation: implement Service Bus + durable database adapters, separate ingestion/worker
identities with scoped RBAC, private endpoints/VNet integration, Entra authentication,
Key Vault, Functions hosting + deployment packaging, Container Apps images, retention/deletion,
and an Azure LLM provider with approved data handling. Choose region/capacity at deployment time.
State belongs in an access-controlled remote backend; never commit state or credentials.


Use a unique 3-20-character lowercase prefix (for example, `devswarm-team-dev`) before planning:
Service Bus namespace names are globally scoped and the default is not reserved. Validate the
subscription GUID explicitly. Terraform validate checks configuration/provider schemas, not
subscription permissions, regional availability, quotas, service naming availability or cost.
See `docs/azure-readiness.md` in the source repository for implemented versus future components.
Keep transport event identity separate from incident fingerprints when adding Service Bus routing.
