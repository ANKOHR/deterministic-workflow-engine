"""Pure event validation and state reduction. No estimates or I/O."""
from datetime import date
import hashlib
import json

class WorkflowError(ValueError):
    """Named validation or transition failure."""

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).replace(chr(0x2014), "\\u2014") + "\n"

def execute(events, as_of):
    try:
        cutoff = date.fromisoformat(as_of)
    except (ValueError, TypeError):
        raise WorkflowError("SchemaError: as_of must be an ISO date") from None
    seen, states, duplicates = {}, {}, 0
    allowed = {"id", "workflow_id", "sequence", "type", "date", "amount_cents", "note"}
    for index, event in enumerate(events, 1):
        prefix = f"SchemaError: record {index}"
        if not isinstance(event, dict):
            raise WorkflowError(f"{prefix}: event must be an object")
        unknown = set(event) - allowed
        if unknown:
            raise WorkflowError(f"{prefix}: unknown field {sorted(unknown)[0]}")
        for field in ("id", "workflow_id", "type", "date"):
            if not isinstance(event.get(field), str) or not event[field] or len(event[field]) > 256:
                raise WorkflowError(f"{prefix}: invalid field {field}")
        for field in ("sequence", "amount_cents"):
            value = event.get(field, 0 if field == "amount_cents" else None)
            if type(value) is not int or not 0 <= value <= 10**12:
                raise WorkflowError(f"{prefix}: invalid field {field}")
        if not isinstance(event.get("note", ""), str) or len(event.get("note", "")) > 100000:
            raise WorkflowError(f"{prefix}: invalid field note")
        try:
            event_date = date.fromisoformat(event["date"])
        except ValueError:
            raise WorkflowError(f"{prefix}: invalid field date") from None
        if event_date > cutoff:
            raise WorkflowError(f"{prefix}: future date exceeds as_of")
        if event["type"] not in {"created", "started", "completed", "failed", "signal"}:
            raise WorkflowError(f"{prefix}: invalid field type")
        if event["id"] in seen:
            if seen[event["id"]] != event:
                raise WorkflowError(f"DuplicateError: conflicting id {event['id']}")
            duplicates += 1
        else:
            seen[event["id"]] = event
    ordered = sorted(seen.values(), key=lambda e: (e["sequence"], e["id"]))
    sequences = set()
    for event in ordered:
        if event["sequence"] in sequences:
            raise WorkflowError("SchemaError: sequence must be globally unique")
        sequences.add(event["sequence"])
        wid, kind = event["workflow_id"], event["type"]
        current = states.get(wid)
        if kind == "created" and current is None:
            states[wid] = {"status": "pending", "signals": 0, "amount_cents": event.get("amount_cents", 0)}
        elif kind == "started" and current and current["status"] == "pending":
            current["status"] = "running"
        elif kind in {"completed", "failed"} and current and current["status"] == "running":
            current["status"] = kind
        elif kind == "signal" and current:
            current["signals"] += 1
        else:
            raise WorkflowError(f"TransitionError: event {event['id']} cannot {kind}")
        if kind != "created" and event.get("amount_cents", 0):
            raise WorkflowError(f"SchemaError: amount_cents only allowed on created: {event['id']}")
    metrics = {"records": len(events), "unique_events": len(seen), "duplicate_events": duplicates,
               "workflows": len(states), "signals": sum(s["signals"] for s in states.values()),
               "amount_cents": sum(s["amount_cents"] for s in states.values())}
    for status in ("pending", "running", "completed", "failed"):
        metrics[status] = sum(s["status"] == status for s in states.values())
    return {"metrics": metrics, "workflows": dict(sorted(states.items())),
            "event_digest": hashlib.sha256(canonical(events).encode()).hexdigest()}
