"""Local CLI with atomic outputs and named errors."""
import argparse
import json
import os
from pathlib import Path
import tempfile
from .core import WorkflowError, canonical, execute
from .fixtures import generate
from .report import render

def read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise WorkflowError(f"ParseError: {path}: line {error.lineno}: {error.msg}") from None
    except UnicodeError:
        raise WorkflowError(f"ParseError: {path}: line 1: invalid UTF-8") from None
    except OSError as error:
        raise WorkflowError(f"InputError: {path}: {error.strerror}; use --input with an existing directory") from None

def load(directory):
    path = Path(directory)
    if not path.is_dir():
        raise WorkflowError(f"InputError: {path}: missing directory; use --input <dir>")
    source = path / "events.json"
    if not source.exists():
        if any(path.iterdir()):
            raise WorkflowError(f"SchemaError: {source}: missing events.json")
        return {"synthetic": False, "source": "empty directory", "as_of": "1970-01-01", "events": []}
    data = read(source)
    if not isinstance(data, dict):
        raise WorkflowError(f"SchemaError: {source}: root must be an object")
    unknown = set(data) - {"synthetic", "label", "source", "as_of", "events"}
    if unknown:
        raise WorkflowError(f"SchemaError: {source}: unknown field {sorted(unknown)[0]}")
    if type(data.get("synthetic")) is not bool or not isinstance(data.get("events"), list):
        raise WorkflowError(f"SchemaError: {source}: synthetic boolean and events array required")
    if not data["synthetic"] and (not isinstance(data.get("source"), str) or not data["source"]):
        raise WorkflowError(f"SchemaError: {source}: real input requires source declaration")
    try:
        execute(data["events"], data.get("as_of"))
    except WorkflowError as error:
        raise WorkflowError(f"{source}: {error}") from None
    return data

def compute(data):
    return {**execute(data["events"], data["as_of"]), "synthetic": data["synthetic"],
            "source": data.get("source", "synthetic fixtures"), "as_of": data["as_of"]}

def atomic_write(path, content):
    target = Path(path)
    temp = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=target.parent, delete=False) as handle:
            temp = Path(handle.name)
            handle.write(content)
        os.replace(temp, target)
    except OSError as error:
        raise WorkflowError(f"WriteError: {target}: {error.strerror}") from None
    finally:
        if temp and temp.exists():
            temp.unlink()

def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic local workflow orchestration. No external calls.")
    subs = parser.add_subparsers(dest="command", required=True)
    fixtures = subs.add_parser("fixtures", help="Generate 200 labelled synthetic events", epilog="Example: dwe fixtures --out demo")
    fixtures.add_argument("--out", required=True)
    for name in ("run", "validate"):
        command = subs.add_parser(name, help="Execute events" if name == "run" else "Validate schema and transitions", epilog=f"Example: dwe {name} --input demo")
        command.add_argument("--input", required=True)
        if name == "run":
            command.add_argument("--state", default=".dwe/run.json")
    report = subs.add_parser("report", help="Render computed result and provenance", epilog="Example: dwe report --format md")
    report.add_argument("--format", choices=("md", "json"), default="md")
    report.add_argument("--state", default=".dwe/run.json")
    report.add_argument("--out")
    replay = subs.add_parser("replay", help="Recompute stored events and verify saved result", epilog="Example: dwe replay --state .dwe/run.json")
    replay.add_argument("--state", default=".dwe/run.json")
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated SYNTHETIC fixture: 200 records")
        elif args.command in ("run", "validate"):
            data = load(args.input)
            result = compute(data)
            if args.command == "run":
                atomic_write(args.state, canonical({"input": data, "result": result}))
            print(("Executed" if args.command == "run" else "Validated") + f" {result['metrics']['records']} records; " + ("SYNTHETIC" if data["synthetic"] else "REAL operator-declared input"))
        else:
            saved = read(args.state)
            if not isinstance(saved, dict) or "input" not in saved or "result" not in saved:
                raise WorkflowError("SchemaError: state requires input and result")
            result = compute(saved["input"])
            if result != saved["result"]:
                raise WorkflowError("ReplayError: saved result differs from recomputed events")
            if args.command == "replay":
                print("Replay verified: byte-identical computed result; " + ("SYNTHETIC" if result["synthetic"] else "REAL operator-declared input"))
            else:
                output = render(result, args.format)
                if args.out:
                    atomic_write(args.out, output)
                else:
                    print(output, end="")
        return 0
    except (WorkflowError, OSError, KeyError, TypeError, ValueError) as error:
        parser.exit(2, f"{error if isinstance(error, WorkflowError) else 'SchemaOrIOError: ' + str(error)}\n")

if __name__ == "__main__":
    main()
