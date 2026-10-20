"""Command-line interface; all incident processing is local and offline by default."""

import argparse
import json
import logging
import os
import sys
import time
from importlib import metadata, resources
from pathlib import Path

from pydantic import ValidationError

from devswarm.sdk import DevSwarm
from devswarm.shared.contracts import BugDraft


def bundled(name):
    return resources.files("devswarm.resources").joinpath(name).read_text(encoding="utf-8")


def initialize(directory, files):
    destination = Path(directory)
    existing = [name for name in files if (destination / name).exists()]
    if existing:
        raise FileExistsError("Destination contains files that would be overwritten")
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        with (destination / name).open("x", encoding="utf-8") as output:
            output.write(content)
    return {"directory": str(destination.resolve()), "files": sorted(files)}


def main(argv=None):
    parser = argparse.ArgumentParser(description="DevSwarm offline incident-to-bug-draft tools")
    parser.add_argument("--version", action="version", version=metadata.version("devswarm"))
    parser.add_argument("--db", default=os.environ.get("DEVSWARM_DB", ".data/devswarm.db"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("sample", help="Print a bundled sanitized incident fixture")
    commands.add_parser("demo", help="Run the bundled incident through the offline pipeline")
    ingest = commands.add_parser("ingest", help="Accept a sanitized incident JSON file")
    ingest.add_argument("file", type=Path)
    worker = commands.add_parser("worker", help="Generate one pending draft, or watch continuously")
    mode = worker.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true")
    mode.add_argument("--watch", action="store_true")
    show = commands.add_parser("show", help="Read an incident and its draft")
    show.add_argument("fingerprint")
    export = commands.add_parser("export", help="Print a reviewable draft as JSON")
    export.add_argument("fingerprint")
    serve = commands.add_parser("serve", help="Run the optional local API")
    serve.add_argument("--port", type=int, default=8000)
    mcp = commands.add_parser("mcp", help="Run an optional local MCP server over stdio")
    mcp.add_argument("server", choices=["evidence", "drafts"])
    functions = commands.add_parser(
        "init-functions", help="Create a local Functions host directory"
    )
    functions.add_argument("directory")
    azure = commands.add_parser("init-azure", help="Export the Terraform Azure foundation scaffold")
    azure.add_argument("directory")
    args = parser.parse_args(argv)
    os.environ["DEVSWARM_DB"] = args.db
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        if args.command == "sample":
            print(bundled("incident.json").strip())
            return 0
        if args.command == "serve":
            import uvicorn

            uvicorn.run("devswarm.apps.api.main:app", host="127.0.0.1", port=args.port)
            return 0
        if args.command == "mcp":
            if args.server == "evidence":
                from devswarm.tool_servers.evidence import mcp as server
            else:
                from devswarm.tool_servers.drafts import mcp as server
            server.run()
            return 0
        if args.command == "init-functions":
            settings = json.loads(bundled("local.settings.example.json"))
            settings["Values"]["DEVSWARM_DB"] = str(Path(args.db).resolve())
            result = initialize(
                args.directory,
                {
                    "function_app.py": "from devswarm.apps.ingestion.function_app import app as app\n",
                    "host.json": bundled("host.json"),
                    "local.settings.json": json.dumps(settings, indent=2) + "\n",
                    "requirements.txt": f"devswarm[azure]=={metadata.version('devswarm')}\n",
                    ".gitignore": "local.settings.json\n__pycache__/\n",
                },
            )
        elif args.command == "init-azure":
            result = initialize(
                args.directory,
                {"main.tf": bundled("azure-main.tf"), "README.md": bundled("azure-README.md")},
            )
        else:
            sdk = DevSwarm(args.db)
            if args.command in {"ingest", "demo"}:
                payload = json.loads(
                    bundled("incident.json")
                    if args.command == "demo"
                    else args.file.read_text(encoding="utf-8-sig")
                )
                receipt = sdk.ingest(payload)
                result = receipt.model_dump()
                if args.command == "demo":
                    while sdk.process_next():
                        pass
                    result = sdk.get(receipt.fingerprint)
            elif args.command == "worker":
                if args.watch:
                    while True:
                        sdk.process_next()
                        time.sleep(1)
                result = {"processed": sdk.process_next()}
            else:
                result = sdk.get(args.fingerprint)
                if result is None:
                    print('{"error":"incident_not_found"}', file=sys.stderr)
                    return 1
                if args.command == "export":
                    if result["draft"] is None:
                        print('{"error":"draft_pending"}', file=sys.stderr)
                        return 1
                    from devswarm.agents.courier import export

                    print(export(BugDraft.model_validate(result["draft"])))
                    return 0
        print(json.dumps(result, indent=2))
        return 0
    except ModuleNotFoundError:
        extra = {"serve": "api", "mcp": "mcp"}.get(args.command, "all")
        print(f'Install optional support with: pip install "devswarm[{extra}]"', file=sys.stderr)
        return 2
    except (ValidationError, ValueError):
        print('{"error":"invalid_input"}', file=sys.stderr)
        return 2
    except FileExistsError:
        print('{"error":"refusing_to_overwrite_existing_files"}', file=sys.stderr)
        return 2
    except OSError:
        print('{"error":"local_file_or_database_operation_failed"}', file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
