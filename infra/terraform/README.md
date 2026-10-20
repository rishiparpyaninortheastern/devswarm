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
