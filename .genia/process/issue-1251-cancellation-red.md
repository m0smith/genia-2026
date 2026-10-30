# Cancellation RED evidence

At b55eeb93, before any transport implementation edit:
`uv run --no-sync pytest -q tests/unit/test_spec_runner_timeout_cleanup.py`
returns2FAIL/1PASS in5.32s. Both timeout and injected caller-cancellation rows
correctly retain their expected classification/partial diagnostics but leave a
same-group fixture child alive; the new assertion fails. The success control
passes and preserves existing successful-request descendant behavior. Each
isolated controller cleans/reaps its owned fixture child in finally, including
PID recovery after unexpected transport exceptions. No existing assertion,
capability, shared semantic case, oracle, request default or baseline changed.

This is Linux/Python OS mechanics, not a portable Genia behavior definition.
Unit artificial1s timeout proves cleanup; all real diagnostic/conformance and
acceptance requests retain10s. The original synthetic10s probe separately
recorded adaptergone/childSleeping at10.009s and childexit at15.048s. Neither
observation identifies the cause of the historical1+6Genia request timeouts.
