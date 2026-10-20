"""Exercise a real local Functions host and Azurite with synthetic telemetry only."""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def request(url, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    req = Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=5) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.loads(error.read() or b"{}")


def unused(port):
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError as error:
            raise RuntimeError(
                f"Port {port} is occupied; stop the other local service first"
            ) from error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--func", default=shutil.which("func"))
    parser.add_argument("--node", default=shutil.which("node"))
    parser.add_argument("--azurite", required=True, help="Path to azurite/dist/src/azurite.js")
    parser.add_argument("--host-directory", type=Path, default=ROOT / "apps/ingestion")
    args = parser.parse_args()
    if not args.func or not args.node:
        parser.error("Provide --func and --node, or put those tools on PATH")
    for port in (7075, 8075, 10000, 10001, 10002):
        unused(port)
    run = (
        ROOT
        / ".data"
        / ("functions-smoke-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    )
    run.mkdir(parents=True)
    env = os.environ.copy()
    env.update(
        {
            "PATH": str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", ""),
            "VIRTUAL_ENV": str(Path(sys.executable).parent.parent),
            "PYTHONPATH": str(ROOT),
            "FUNCTIONS_WORKER_RUNTIME": "python",
            "AzureWebJobsStorage": "UseDevelopmentStorage=true",
            "DEVSWARM_DB": str(run / "incidents.db"),
            "AzureWebJobsSecretStorageType": "files",
            "AZURE_FUNCTIONS_ENVIRONMENT": "Development",
            "languageWorkers__python__defaultExecutablePath": sys.executable,
        }
    )
    processes, handles = [], []
    result = {"status": "running", "run_directory": str(run), "checks": []}
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    def launch(name, command, cwd):
        log = (run / f"{name}.log").open("w", encoding="utf-8")
        handles.append(log)
        child = subprocess.Popen(
            command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=flags
        )
        processes.append(child)
        return child

    def wait(url, child, timeout=100):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if child.poll() is not None:
                raise RuntimeError(f"Local process exited with {child.returncode}; inspect {run}")
            try:
                status, body = request(url)
                if status == 200 and body.get("state", "Running").lower() == "running":
                    return
            except (OSError, URLError, ValueError):
                pass
            time.sleep(0.5)
        raise RuntimeError(f"Local host did not become ready; inspect {run}")

    try:
        emulator = launch(
            "azurite",
            [
                args.node,
                str(Path(args.azurite).resolve()),
                "--silent",
                "--location",
                str(run / "azurite"),
                "--debug",
                str(run / "azurite-debug.log"),
            ],
            ROOT,
        )
        deadline = time.monotonic() + 60
        while True:
            if emulator.poll() is not None:
                raise RuntimeError("Azurite exited before becoming ready")
            try:
                with socket.create_connection(("127.0.0.1", 10000), timeout=1):
                    break
            except OSError:
                if time.monotonic() >= deadline:
                    raise RuntimeError("Azurite blob service did not become ready")
                time.sleep(0.5)
        result["checks"].append("Azurite blob service accepted a local connection")
        host = launch(
            "functions",
            [str(Path(args.func).resolve()), "start", "--port", "7075"],
            args.host_directory.resolve(),
        )
        api = launch(
            "api",
            [
                sys.executable,
                "-m",
                "uvicorn",
                "apps.api.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8075",
            ],
            ROOT,
        )
        wait("http://127.0.0.1:7075/admin/host/status", host)
        wait("http://127.0.0.1:8075/health", api)
        result["checks"].append("Real Functions host, Azurite and API started")
        event = json.loads((ROOT / "examples/incident.json").read_text())
        event["message"] = "Inventory timeout token=devswarm-smoke-secret user=smoke@example.com"
        status, first = request("http://127.0.0.1:7075/api/incidents", event)
        assert status == 202, (status, first)
        status, repeated = request("http://127.0.0.1:7075/api/incidents", event)
        assert status == 202 and repeated["duplicate"] and repeated["occurrences"] == 2
        assert first["fingerprint"] == repeated["fingerprint"]
        result["checks"].append("HTTP intake and duplicate detection: 202, count 2")
        status, rejected = request(
            "http://127.0.0.1:7075/api/incidents", event | {"sanitized": False}
        )
        assert status == 422 and "devswarm-smoke-secret" not in json.dumps(rejected)
        result["checks"].append("Unsanitized payload rejected with generic 422")
        key = first["fingerprint"]
        status, pending = request(f"http://127.0.0.1:8075/incidents/{key}")
        assert status == 200 and pending["state"] == "pending"
        with (run / "worker.log").open("w", encoding="utf-8") as worker_log:
            subprocess.run(
                [sys.executable, "-m", "apps.worker.main", "--once"],
                cwd=ROOT,
                env=env,
                stdout=worker_log,
                stderr=subprocess.STDOUT,
                timeout=30,
                check=True,
                creationflags=flags,
            )
        status, ready = request(f"http://127.0.0.1:8075/incidents/{key}")
        assert status == 200 and ready["state"] == "draft_ready"
        assert ready["draft"]["status"] == "needs_human_review"
        assert "[REDACTED]" in ready["draft"]["evidence"][0]["excerpt"]
        result["checks"].append(
            "Worker generated evidence-backed review draft; API reads shared persistence"
        )
        (run / "draft.json").write_text(json.dumps(ready, indent=2))
        status, third = request("http://127.0.0.1:7075/api/incidents", event)
        assert status == 202 and third["occurrences"] == 3 and third["state"] == "draft_ready"
        result["checks"].append("Repeat after drafting preserves draft and increments count to 3")
        host.terminate()
        host.wait(timeout=15)
        host = launch(
            "functions-restarted",
            [str(Path(args.func).resolve()), "start", "--port", "7075"],
            args.host_directory.resolve(),
        )
        wait("http://127.0.0.1:7075/admin/host/status", host)
        status, restarted = request("http://127.0.0.1:7075/api/incidents", event)
        assert (
            status == 202 and restarted["occurrences"] == 4 and restarted["state"] == "draft_ready"
        )
        result["checks"].append("Draft and occurrence count survive Functions host restart")
        for path in [run / "incidents.db", *run.glob("*.log")]:
            data = path.read_bytes()
            assert b"devswarm-smoke-secret" not in data, f"Synthetic secret leaked into {path.name}"
            assert b"smoke@example.com" not in data, f"Synthetic email leaked into {path.name}"
        result["checks"].append("Synthetic secrets absent from database, draft and service logs")
        assert "devswarm-smoke-secret" not in json.dumps(ready)
        result["status"] = "passed"
    except Exception as error:
        result["status"] = "failed"
        result["error_type"] = type(error).__name__
        raise
    finally:
        for child in reversed(processes):
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
        for handle in handles:
            handle.close()
        (run / "report.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
