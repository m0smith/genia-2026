"""Fresh, bounded post-merge fixture verification using the canonical protocol path."""
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from pathlib import Path
import json
import sys
from tools.spec_runner.loader import load_spec
from tools.spec_runner.host_executor import execute_spec_via_host
from tools.spec_runner.protocol import build_request, run_adapter_request

host, count = sys.argv[1], int(sys.argv[2])
command = [host] if 'genia-adapter' in host else [host, '-m', 'hosts.python.protocol_adapter']
spec = load_spec(Path('spec/eval/r25-process-fifo-fail-stop.yaml'))
caps = {'process_primitives': 'supported', 'refs': 'supported'}
def run(index):
    result = execute_spec_via_host(spec, command, timeout=10.0, host_capabilities=caps)
    return {'index': index, 'kind': result.kind, 'reason': result.reason, 'failures': repr(result.failures)}
with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(run, range(count)))
source = 'p = spawn((msg) -> 1 / 0)\nsend(p, 1)\n_r25_await_idle()\nsend(p, 2)\nprint("unreachable")'
negative = run_adapter_request(command, build_request('post-failure-send', 'eval', {'source': source, 'stdin': None, 'argv': None, 'fixtures': ['r25_concurrency']}), timeout=10.0)
expected_error = 'Error: send: process is failed\n' if 'genia-adapter' in host else 'Error: Process has failed: ZeroDivisionError: exact division by zero\n'
negative_ok = negative.kind == 'ok' and negative.result == {'stdout': '', 'stderr': expected_error, 'exit_code': 1}
report = {'host': command, 'requests': count, 'max_concurrent': 8, 'timeout_seconds': 10, 'counts': dict(Counter(x['kind'] for x in results)), 'results': results, 'post_failure_send': {'ok': negative_ok, 'response': repr(negative)}}
print(json.dumps(report, indent=2))
sys.exit(0 if report['counts'] == {'pass': count} and negative_ok else 1)
