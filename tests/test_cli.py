import json

from devswarm.cli import main

from devswarm import DevSwarm


def test_cli_offline_workflow(tmp_path, capsys):
    db = str(tmp_path / "cli.db")
    assert main(["--db", db, "demo"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["state"] == "draft_ready"
    key = result["fingerprint"]
    assert main(["--db", db, "export", key]) == 0
    draft = json.loads(capsys.readouterr().out)
    assert draft["status"] == "needs_human_review"
    assert main(["--db", db, "worker", "--once"]) == 0
    assert json.loads(capsys.readouterr().out) == {"processed": False}


def test_cli_does_not_echo_invalid_input(tmp_path, capsys):
    payload = tmp_path / "invalid.json"
    payload.write_text('{"password":"synthetic-secret"}')
    assert main(["--db", str(tmp_path / "data.db"), "ingest", str(payload)]) == 2
    output = capsys.readouterr()
    assert "synthetic-secret" not in output.err
    assert "invalid_input" in output.err


def test_initializer_is_safe(tmp_path, capsys):
    destination = tmp_path / "host"
    assert main(["init-functions", str(destination)]) == 0
    capsys.readouterr()
    assert "devswarm.apps.ingestion" in (destination / "function_app.py").read_text()
    before = (destination / "host.json").read_bytes()
    assert main(["init-functions", str(destination)]) == 2
    assert (destination / "host.json").read_bytes() == before
    assert "refusing_to_overwrite" in capsys.readouterr().err


def test_azure_scaffold(tmp_path, capsys):
    assert main(["init-azure", str(tmp_path / "azure")]) == 0
    assert "azurerm" in (tmp_path / "azure/main.tf").read_text()


def test_sdk_round_trip(tmp_path, event=None):
    from importlib.resources import files

    payload = json.loads(files("devswarm.resources").joinpath("incident.json").read_text())
    sdk = DevSwarm(tmp_path / "sdk.db")
    key = sdk.ingest(payload).fingerprint
    assert sdk.process_next()
    assert sdk.get(key)["state"] == "draft_ready"


def test_missing_incident_exit(tmp_path, capsys):
    assert main(["--db", str(tmp_path / "empty.db"), "show", "missing"]) == 1
    assert "incident_not_found" in capsys.readouterr().err
