# #1299 RED evidence

Python host schedule regression reads actual shared YAML and forces the worker
ahead after boom acceptance, using Events only (no sleep/polling). Old source
fails deterministically at send3: RuntimeError: Process has failed:
ZeroDivisionError: exact division by zero. Command: uv run --no-sync pytest -q
 tests/unit/test_r25_concurrency_fixture.py. Result1FAIL/4PASS (1.22s).
The failure is expected: accepted boom can terminate before root's last send.
No production/runtime changes precede this RED commit.
