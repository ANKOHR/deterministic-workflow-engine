import json
import time
import pytest
from deterministic_workflow_engine.cli import main
from deterministic_workflow_engine.fixtures import generate

def test_run_completes_on_fixture(tmp_path, capsys):
    generate(tmp_path / "input")
    start = time.perf_counter()
    assert main(["run", "--input", str(tmp_path / "input"), "--state", str(tmp_path / "state.json")]) == 0
    assert main(["report", "--state", str(tmp_path / "state.json"), "--format", "md"]) == 0
    assert time.perf_counter() - start < 5
    assert "SYNTHETIC" in capsys.readouterr().out

def test_empty_input_renders_without_traceback(tmp_path, capsys):
    source = tmp_path / "empty"; source.mkdir()
    main(["run", "--input", str(source), "--state", str(tmp_path / "state")])
    main(["report", "--state", str(tmp_path / "state"), "--format", "json"])
    assert '"records": 0' in capsys.readouterr().out

def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "events.json").write_text('{\n bad')
    with pytest.raises(SystemExit) as error:
        main(["validate", "--input", str(tmp_path)])
    assert error.value.code == 2
    text = capsys.readouterr().err
    assert "ParseError" in text and "events.json: line 2" in text

def test_determinism_byte_identical(tmp_path):
    generate(tmp_path / "input")
    for name in ("a", "b"):
        main(["run", "--input", str(tmp_path / "input"), "--state", str(tmp_path / name)])
        main(["report", "--state", str(tmp_path / name), "--out", str(tmp_path / (name + '.md'))])
    assert (tmp_path / "a").read_bytes() == (tmp_path / "b").read_bytes()
    assert (tmp_path / "a.md").read_bytes() == (tmp_path / "b.md").read_bytes()

def test_cli_smoke_all_subcommands(tmp_path):
    main(["fixtures", "--out", str(tmp_path / "input")])
    main(["validate", "--input", str(tmp_path / "input")])
    main(["run", "--input", str(tmp_path / "input"), "--state", str(tmp_path / "state")])
    main(["replay", "--state", str(tmp_path / "state")])
    main(["report", "--state", str(tmp_path / "state"), "--format", "json"])
    for command in ("fixtures", "validate", "run", "replay", "report"):
        with pytest.raises(SystemExit) as error:
            main([command, "--help"])
        assert error.value.code == 0

def test_missing_input(tmp_path, capsys):
    with pytest.raises(SystemExit):
        main(["run", "--input", str(tmp_path / "missing")])
    assert "InputError" in capsys.readouterr().err

def test_write_failure_no_partial_file(tmp_path, capsys):
    generate(tmp_path / "input")
    main(["run", "--input", str(tmp_path / "input"), "--state", str(tmp_path / "state")])
    target = tmp_path / "directory"; target.mkdir()
    with pytest.raises(SystemExit):
        main(["report", "--state", str(tmp_path / "state"), "--out", str(target)])
    assert "WriteError" in capsys.readouterr().err
    assert sorted(p.name for p in tmp_path.iterdir()) == ["directory", "input", "state"]

def test_replay_detects_tampering(tmp_path, capsys):
    generate(tmp_path / "input")
    main(["run", "--input", str(tmp_path / "input"), "--state", str(tmp_path / "state")])
    path = tmp_path / "state"; data = json.loads(path.read_text()); data["result"]["metrics"]["completed"] = 0
    path.write_text(json.dumps(data))
    with pytest.raises(SystemExit):
        main(["replay", "--state", str(path)])
    assert "ReplayError" in capsys.readouterr().err


def test_schema_drift_names_file_and_field(tmp_path, capsys):
    generate(tmp_path)
    path = tmp_path / "events.json"; data = json.loads(path.read_text()); data["events"][0]["unexpected"] = 1
    path.write_text(json.dumps(data))
    with pytest.raises(SystemExit):
        main(["validate", "--input", str(tmp_path)])
    error = capsys.readouterr().err
    assert "SchemaError" in error and "unexpected" in error and "events.json" in error


def test_unicode_em_dash_is_escaped(tmp_path, capsys):
    generate(tmp_path / "input")
    path = tmp_path / "input" / "events.json"; data = json.loads(path.read_text()); data["events"][0]["workflow_id"] += chr(0x2014)
    for event in data["events"]:
        if event["workflow_id"] == "w00":
            event["workflow_id"] += chr(0x2014)
    path.write_text(json.dumps(data))
    main(["run", "--input", str(tmp_path / "input"), "--state", str(tmp_path / "state")])
    main(["report", "--state", str(tmp_path / "state")])
    assert chr(0x2014) not in capsys.readouterr().out
