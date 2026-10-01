# Deterministic Workflow Engine

A CPU-only Python CLI for local event-driven workflow orchestration and replay. It reduces an explicit event log into workflow states. It does not execute external tasks, call services, predict events, or provide distributed scheduling.

Hypothesis: explicit event ordering, strict validation, and replay make local workflow state trustworthy. Synthetic acceptance evidence supports this hypothesis within the documented state machine. Real-use evidence is still pending.

## Quickstart

Python 3.10 or later and setuptools are required. Development tests require pytest. No runtime dependencies or network calls are used.

```powershell
python -m pip install --no-deps --no-build-isolation -e .
dwe fixtures --out demo
dwe run --input demo
dwe report --format md
dwe replay
python -m pytest -q
```

If pip warns that its Scripts directory is absent from PATH, add that reported directory to PATH for the current shell or invoke dwe.exe by its full path.

Run without installing using `python -m deterministic_workflow_engine.cli` in place of `dwe`.
The default saved run is `.dwe/run.json` relative to the current directory. Each run replaces that snapshot atomically. Reports re-execute its events and reject mismatched results.

## Input reference

A directory contains `events.json`, a UTF-8 JSON object:

```json
{
  "synthetic": false,
  "source": "Henry's own events, entered by Henry",
  "as_of": "2026-09-30",
  "events": [
    {"id": "a", "workflow_id": "invoice-1", "sequence": 0, "type": "created", "date": "2026-09-30", "amount_cents": 300},
    {"id": "b", "workflow_id": "invoice-1", "sequence": 1, "type": "started", "date": "2026-09-30"},
    {"id": "c", "workflow_id": "invoice-1", "sequence": 2, "type": "signal", "date": "2026-09-30", "note": "Reviewed"},
    {"id": "d", "workflow_id": "invoice-1", "sequence": 3, "type": "signal", "date": "2026-09-30", "note": "Approved"},
    {"id": "e", "workflow_id": "invoice-1", "sequence": 4, "type": "completed", "date": "2026-09-30"}
  ]
}
```

This example is illustrative, not a measured real trial. The five-record synthetic counterpart is shipped in `examples/tiny/events.json`. Real inputs require an operator source declaration. The tool cannot verify ownership. No real trial data is shipped.

Required event fields: `id`, `workflow_id`, `sequence`, `type`, `date`. Optional: `amount_cents` (default zero), `note` (default empty). Unknown event fields are rejected. IDs, workflow IDs, type and date are nonempty strings of at most 256 characters; note accepts up to 100,000 characters, including Unicode and Windows paths. Sequence and cents must be integers from zero through 1,000,000,000,000; booleans are rejected. Dates must be ISO dates no later than the explicit `as_of` date. The wall clock never affects results.

Events are applied by globally unique sequence, independent of input order. Exactly identical duplicate IDs are ignored after counting them. Conflicting duplicate IDs are errors. `created` establishes pending state and carries optional cents; `started` moves pending to running; `completed` or `failed` moves running to a terminal state. `signal` increments a counter on any existing workflow, including terminal workflows. Other transitions fail the entire run. Nonzero cents on events other than `created` are rejected. Cents are input allocations, not revenue or savings. A single currency must be selected by the operator; currency conversion is not supported.

An empty directory produces zero counts with an explicit empty-directory source. A nonempty directory without events.json is a schema error. Only JSON is supported; CSV and YAML are not silently interpreted. Expectations files are never used by the engine.

## Commands

| Command | Purpose | Example |
| --- | --- | --- |
| fixtures | Generate 200 labelled synthetic records | `dwe fixtures --out demo` |
| validate | Check schema, duplicates and transitions without writing state | `dwe validate --input demo` |
| run | Reduce events and atomically save inputs plus results | `dwe run --input demo --state trial/run.json` |
| replay | Recompute stored input and verify saved result exactly | `dwe replay --state trial/run.json` |
| report | Render markdown or JSON with provenance | `dwe report --format json --out trial/report.json` |

Every command supports `--help`. Report and replay accept `--state`. Reports go to stdout unless `--out` is supplied. Named errors exit with code 2 and no traceback.

## Architecture

```text
fixtures.py -> labelled events.json + independent expectations.json
                         |
cli.py -> JSON parsing -> core.py validation + deterministic reduction
                         |
                   atomic run snapshot
                         |
                 replay recomputation -> report.py -> Markdown / JSON
```

Core logic has no I/O. Canonical sorted UTF-8 JSON, LF newlines, explicit dates, and no randomness give byte-identical outputs for identical inputs. The snapshot digest covers the input event list, so reordering input changes that digest even if the resulting workflow states agree. No random seed is needed. Em dash characters supplied by users are escaped as Unicode sequences on report surfaces.

## Acceptance evidence and fixture policy

The synthetic fixture has 40 workflows, each with four unique events and one exact duplicate: 200 records, 160 unique events, 40 duplicates. Workflows 0 through 19 complete; 20 through 29 fail; 30 through 39 remain running. Each has one signal, and the last ten have a second signal, for 50 signals. Allocations are 100 times the integers 1 through 40, totaling 82,000 cents. All statuses sum to 40. Hand-computed expectations and their derivation are stored separately.

JSON cannot carry header comments legally, so each fixture JSON uses `synthetic: true` and a SYNTHETIC label. Markdown fixture files carry a SYNTHETIC header comment. The tiny example follows the same policy. The generator uses no random source. See `EVIDENCE.md` for measured local test and timing results.

## Honesty boundary

Every figure is computed from explicit inputs. Synthetic reports identify synthetic provenance, and real reports display the operator's declaration with an ownership verification caveat. No accuracy claim extends beyond the planted fixture and tested rules. Time saved and money saved are unmeasured and are not reported. The CLI has no savings estimator. Any future hypothetical illustration must be labelled hypothetical in code, CLI output, reports, and documentation.

## Failure modes and limits

Malformed JSON reports ParseError with file and line. Invalid fields report SchemaError with the offending field and input filename. JSON semantic fields do not have reliable source line locations, so record indices identify them instead. Missing directories report InputError with a usage hint. Invalid transitions and conflicting duplicates report TransitionError and DuplicateError. Replay mismatch reports ReplayError. Output failure reports WriteError and removes temporary files, preserving the previous file. Fixture generation uses normal file writes and should be directed at a dedicated directory.

This engine is synchronous and local. It has no worker execution, concurrent writer locking, retry scheduler, database, authentication or tamper-proof audit storage. A malicious operator can rewrite both events and results; replay detects inconsistency, not authenticity. Memory use scales with the full event log. Validation is all-or-nothing; invalid records are never silently dropped.

## Two-week improvement hook and verdict

After two weeks of actual use, measure status accuracy against a hand-checked sample: incorrect workflow statuses divided by sampled workflow statuses. Record dates, usage count, sample size, errors, and causes in an unshipped trial log. If the error rate exceeds 10 percent, fix the leading measured cause and repeat the sample. If the tool is unused, record why and kill it. Time savings can be reported only with a measured baseline and the same workload.

Current provisional verdict: **maintain** as tested portfolio evidence. The two-week window has not occurred; this is not a completed real-use verdict. After that window, record a dated verdict and reason: expand for daily use or revenue, integrate for heavy sibling overlap, commercialise for demonstrated buyer willingness to pay, maintain for useful portfolio evidence, or kill for no use or inability to meet acceptance criteria.
