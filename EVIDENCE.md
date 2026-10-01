# Local acceptance evidence

Measured on 2026-10-01, Windows, Python 3.12.10, CPU only.

31 pytest cases passed. Installed dwe.exe fixture generation, run and Markdown report completed in 0.843916 seconds total, below 5 seconds. This is elapsed execution time on this machine, not time saved against a baseline. Full 200-record state replay succeeded. The five-record example also executed and rendered without tracebacks.

Computed synthetic ground truth: 200 records, 160 unique events, 40 duplicates, 40 workflows, 20 completed, 10 failed, 10 running, zero pending, 50 signals, 82000 allocated cents. Tests compare all figures against independent expectations and compare the exact failed and completed workflow sets to the planted sets, with zero false positives or missing planted outcomes.

Corrupting one completion into a failure produced 19 completed and 11 failed. Repeated runs and reports were byte-identical. Malformed JSON, schema drift, future dates, negative values, conflicting duplicate IDs, invalid transitions, long strings, Unicode, empty input, output failures and saved-result tampering were tested.

No real-use accuracy, buyer demand, savings or two-week verdict is measured. Provisional verdict: maintain as portfolio evidence, pending the documented evidence window.
