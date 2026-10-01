import json
from deterministic_workflow_engine.fixtures import generate, EXPECTED
from deterministic_workflow_engine.core import execute

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    for path in tmp_path.iterdir():
        if path.suffix == ".json":
            assert json.loads(path.read_text())["synthetic"] is True
            assert "SYNTHETIC" in path.read_text()
        else:
            assert path.read_text().startswith("<!-- SYNTHETIC")

def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    generate(tmp_path)
    data = json.loads((tmp_path / "events.json").read_text())
    assert execute(data["events"], data["as_of"])["metrics"] == EXPECTED
    assert EXPECTED["amount_cents"] == 100 * 40 * 41 // 2

def test_corruption_changes_computed_figures(tmp_path):
    generate(tmp_path)
    data = json.loads((tmp_path / "events.json").read_text())
    for event in data["events"]:
        if event["id"] == "e00-2":
            event["type"] = "failed"
    result = execute(data["events"], data["as_of"])
    assert result["metrics"]["completed"] == 19
    assert result["metrics"]["failed"] == 11
