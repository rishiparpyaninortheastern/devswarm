# Credits and provenance

## Where this implementation came from

This repository was implemented for Rishi Parpyani's DevSwarm incident-triage experiment,
with AI coding assistance, from the project brief and iterative local testing.
The available implementation history does not identify an upstream repository whose
code was copied or forked. The full earlier ideation conversation was not available
for this review, so this is not a claim that the broader idea has no prior inspiration.

The current MVP uses deterministic local adapters. The named agents are components
with separate responsibilities; they do not currently run an autonomous LLM engineering team.

## Open-source foundations

Thank you to the maintainers and contributors of these projects:

| Project | Use in DevSwarm |
| --- | --- |
| [Pydantic](https://github.com/pydantic/pydantic) | Shared validated incident and draft contracts |
| [FastAPI](https://github.com/fastapi/fastapi) | Optional HTTP API |
| [Uvicorn](https://github.com/Kludex/uvicorn) | Local API server |
| [FastMCP](https://github.com/PrefectHQ/fastmcp) | Optional evidence and draft MCP servers |
| [Azure Functions Python library](https://github.com/Azure/azure-functions-python-library) | Optional Functions ingestion adapter |
| [Azure Functions Core Tools](https://github.com/Azure/azure-functions-core-tools) | Local Functions hosting and smoke verification |
| [Azurite](https://github.com/Azure/Azurite) | Local Azure Storage emulation during verification |
| [AzureRM provider](https://github.com/hashicorp/terraform-provider-azurerm) | Terraform Azure foundation scaffold |
| [PyPA build](https://github.com/pypa/build), [Twine](https://github.com/pypa/twine), and [PyPI publishing action](https://github.com/pypa/gh-action-pypi-publish) | Distribution building, validation, and prepared release workflow |
| [pytest](https://github.com/pytest-dev/pytest) and [Ruff](https://github.com/astral-sh/ruff) | Tests and code checks |

Python and its standard-library SQLite integration provide the local runtime and persistence.
These projects retain their own licenses and copyrights; this acknowledgment does not
relicense their work or imply their endorsement.

## Related work, not verified direct inspiration

The idea of software teams composed of agents has substantial prior work, including
[ChatDev](https://github.com/OpenBMB/ChatDev) and
[MetaGPT](https://github.com/FoundationAgents/MetaGPT).
These are useful related projects identified during this attribution review. They are
not dependencies of this MVP, and the available history does not establish that this
implementation was derived from either project. Please do not describe DevSwarm as
built on those frameworks.

## Name clarification

[devswarm-ai/devswarm](https://github.com/devswarm-ai/devswarm) is an existing, separate
AI development product. This incident-triage experiment is independent and unaffiliated;
that project's code was not identified as a source for this implementation.
The shared name may cause confusion and should be reviewed before a PyPI release.

If a specific upstream source is subsequently identified, record its exact repository,
what was adapted, and any applicable attribution and license notices here.
