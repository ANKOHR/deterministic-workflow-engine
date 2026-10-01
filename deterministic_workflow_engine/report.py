"""Render computed outputs with explicit provenance and honesty boundaries."""
from .core import canonical

def render(result, format="md"):
    banner = "Data provenance: " + ("SYNTHETIC fixtures; no real inputs." if result["synthetic"] else
        "REAL input declared by the operator: " + result["source"] + ". Ownership is not independently verified.")
    honesty = "Counts and cents are computed from inputs. Time saved and money saved are unmeasured and are not reported."
    if format == "json":
        return canonical({**result, "provenance_banner": banner, "honesty": honesty})
    lines = ["# Deterministic Workflow Engine", "", banner, "", honesty, "", "| Metric | Computed value |", "| --- | ---: |"]
    lines.extend(f"| {key} | {value} |" for key, value in sorted(result["metrics"].items()))
    lines.extend(["", "Event SHA-256: " + result["event_digest"], "", "Workflow states:", "", "```json", canonical(result["workflows"]).rstrip(), "```", ""])
    return "\n".join(lines).replace(chr(0x2014), "\\u2014")
