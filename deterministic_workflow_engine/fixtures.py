"""Labelled synthetic fixtures; no randomness used."""
from pathlib import Path
from .core import canonical

EXPECTED = {"records": 200, "unique_events": 160, "duplicate_events": 40,
            "workflows": 40, "signals": 50, "amount_cents": 82000,
            "pending": 0, "running": 10, "completed": 20, "failed": 10}

def generate(out):
    target = Path(out)
    target.mkdir(parents=True, exist_ok=True)
    events = []
    for i in range(40):
        kinds = ["created", "started", "completed" if i < 20 else "failed" if i < 30 else "signal", "signal"]
        group = [{"id": f"e{i:02}-{j}", "workflow_id": f"w{i:02}", "sequence": i*4+j,
                  "type": kind, "date": "2026-09-30", "amount_cents": (i+1)*100 if j == 0 else 0,
                  "note": "Synthetic fixture"} for j, kind in enumerate(kinds)]
        events.extend(group + [dict(group[0])])
    (target / "events.json").write_text(canonical({"synthetic": True, "label": "SYNTHETIC fixture",
        "as_of": "2026-09-30", "events": events}), encoding="utf-8")
    (target / "expectations.json").write_text(canonical({"synthetic": True, "label": "SYNTHETIC hand-computed expectations",
        "derivation": "40 groups x 5 records; 4 unique per group; 20 completed, 10 failed, 10 running; 40+10 signals; 100 x (1+...+40) = 82000 cents",
        "metrics": EXPECTED}), encoding="utf-8")
    (target / "README.md").write_text("<!-- SYNTHETIC fixture -->\nAll data in this directory is synthetic. No random seed is needed.\n", encoding="utf-8")
