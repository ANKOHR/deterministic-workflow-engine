import copy
import pytest
from deterministic_workflow_engine.core import execute, WorkflowError

def tiny():
    return [{"id": str(i), "workflow_id": "one", "sequence": i, "type": kind, "date": "2026-09-30", "amount_cents": 300 if i == 0 else 0}
            for i, kind in enumerate(["created", "started", "signal", "signal", "completed"])]

def test_tiny_hand_written_workflow():
    result = execute(tiny(), "2026-09-30")
    assert result["metrics"] == dict(records=5, unique_events=5, duplicate_events=0, workflows=1, signals=2, amount_cents=300, pending=0, running=0, completed=1, failed=0)

@pytest.mark.parametrize("field,value", [("amount_cents", -1), ("amount_cents", True), ("date", "2027-01-01"), ("id", "x"*257), ("sequence", -1), ("note", "x"*100001), ("extra", 1)], ids=["negative-money", "boolean-money", "future", "long-id", "negative-sequence", "long-note", "unknown-field"])
def test_rejects_adversarial_values(field, value):
    events = tiny(); events[0][field] = value
    with pytest.raises(WorkflowError):
        execute(events, "2026-09-30")

def test_conflicting_duplicate():
    events = tiny(); duplicate = copy.deepcopy(events[0]); duplicate["amount_cents"] = 1; events.append(duplicate)
    with pytest.raises(WorkflowError, match="DuplicateError"):
        execute(events, "2026-09-30")

def test_invalid_transition():
    with pytest.raises(WorkflowError, match="TransitionError"):
        execute(tiny()[1:], "2026-09-30")

def test_handles_unicode_and_long_inputs():
    events = tiny(); events[0]["note"] = "中文 café C:\\Users\\henry " + "a"*50000
    assert execute(events, "2026-09-30")["metrics"]["completed"] == 1

def test_sequence_collision():
    events = tiny(); events[1]["sequence"] = 0
    with pytest.raises(WorkflowError, match="sequence"):
        execute(events, "2026-09-30")
