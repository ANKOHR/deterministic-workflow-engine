from deterministic_workflow_engine.cli import compute, load
from deterministic_workflow_engine.fixtures import generate, EXPECTED
from deterministic_workflow_engine.report import render
import json

def result(tmp_path):
    generate(tmp_path)
    return compute(load(tmp_path))

def test_report_matches_ground_truth_exact(tmp_path):
    assert json.loads(render(result(tmp_path), "json"))["metrics"] == EXPECTED

def test_report_zero_false_positives(tmp_path):
    states = result(tmp_path)["workflows"]
    assert {key for key, state in states.items() if state["status"] == "failed"} == {f"w{i:02}" for i in range(20, 30)}
    assert {key for key, state in states.items() if state["status"] == "completed"} == {f"w{i:02}" for i in range(20)}

def test_report_carries_provenance_banner(tmp_path):
    for fmt in ("md", "json"):
        assert "Data provenance: SYNTHETIC" in render(result(tmp_path), fmt)

def test_hypothetical_figures_labelled(tmp_path):
    for fmt in ("md", "json"):
        text = render(result(tmp_path), fmt)
        assert "Time saved and money saved are unmeasured and are not reported" in text

def test_real_provenance(tmp_path):
    value = result(tmp_path); value.update(synthetic=False, source="Henry's hand-entered events")
    assert "Ownership is not independently verified" in render(value)

def test_no_em_dashes_in_outputs(tmp_path):
    for fmt in ("md", "json"):
        assert chr(0x2014) not in render(result(tmp_path), fmt)
