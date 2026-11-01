"""Verify a separately installed wheel from a directory outside the source tree."""

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True, help="Fresh environment's Python")
    args = parser.parse_args()
    # Linux venv Python is often a symlink to the base interpreter. Keep the
    # supplied venv path so the CLI and imports come from that environment.
    python = args.python.absolute()
    cli = python.parent / ("devswarm.exe" if os.name == "nt" else "devswarm")
    run = ROOT / ".data" / ("wheel-smoke-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    run.mkdir(parents=True)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)

    def call(*command, expected=0):
        result = subprocess.run(
            [str(cli), *command], cwd=run, env=env, capture_output=True, text=True, timeout=30
        )
        assert result.returncode == expected, (command, result.returncode, result.stderr)
        return result

    first = json.loads(call("--db", "demo.db", "demo").stdout)
    assert first["state"] == "draft_ready"
    key = first["fingerprint"]
    assert (
        json.loads(call("--db", "demo.db", "export", key).stdout)["status"] == "needs_human_review"
    )
    assert json.loads(call("--db", "demo.db", "demo").stdout)["occurrences"] == 2
    call("init-functions", "host")
    call("init-functions", "host", expected=2)
    call("init-azure", "azure-foundation")
    assert "swarmsleuth[api]" in call("serve", expected=2).stderr
    assert "swarmsleuth[mcp]" in call("mcp", "drafts", expected=2).stderr
    code = """
import devswarm
import importlib.util
from pathlib import Path
assert 'site-packages' in str(Path(devswarm.__file__))
for name in ('fastapi', 'fastmcp', 'azure'):
    assert importlib.util.find_spec(name) is None, name
print(devswarm.__file__)
"""
    imported = subprocess.run(
        [str(python), "-c", code], cwd=run, env=env, capture_output=True, text=True, timeout=30
    )
    assert imported.returncode == 0, imported.stderr
    result = {
        "status": "passed",
        "checks": [
            "offline demo",
            "repeat deduplication",
            "JSON export",
            "Functions and Terraform templates",
            "no-overwrite guard",
            "optional-extra guidance",
            "isolated site-packages import; optional integrations absent",
        ],
    }
    (run / "report.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
