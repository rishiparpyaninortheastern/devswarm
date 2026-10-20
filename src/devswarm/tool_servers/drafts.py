from fastmcp import FastMCP

from devswarm.agents.guardian import sanitize
from devswarm.agents.sentinel import fingerprint
from devswarm.shared.contracts import Incident
from devswarm.shared.llm import LocalDraftProvider

mcp = FastMCP("DevSwarm local draft preview")


@mcp.tool
def preview_draft(incident: Incident) -> dict:
    """Preview a sanitized draft without persistence or external writes."""
    safe = sanitize(incident)
    return LocalDraftProvider().generate(safe, fingerprint(safe)).model_dump()


if __name__ == "__main__":
    mcp.run()
