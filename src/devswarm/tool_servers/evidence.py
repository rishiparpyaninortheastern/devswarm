from fastmcp import FastMCP

from devswarm.shared.runtime import store

mcp = FastMCP("DevSwarm evidence (local read only)")


@mcp.tool
def get_incident(fingerprint: str) -> dict:
    """Read sanitized evidence and a draft from the local store."""
    return store().get(fingerprint) or {"error": "not_found"}


if __name__ == "__main__":
    mcp.run()
