"""Linux-only host-internal adapter cancellation mechanics, not Genia semantics.

The isolated controller reaps its own adopted fixture child so a non-reaping
container PID1 cannot turn the ownership assertion into a zombie-count test.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux /proc child-state observation')
@pytest.mark.parametrize('mode', ['timeout', 'cancel', 'success'])
def test_adapter_descendant_ownership_on_timeout_and_success(tmp_path: Path, mode: str) -> None:
    """Cancel owned child work on timeout while preserving the existing successful-request boundary."""
    adapter = tmp_path / 'adapter.py'
    pidfile = tmp_path / 'child.pid'
    adapter.write_text(
        'import json,subprocess,sys,threading\n'
        'from pathlib import Path\n'
        'child=subprocess.Popen([sys.executable,"-c","import threading; threading.Event().wait(60)"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n'
        'Path(sys.argv[1]).write_text(str(child.pid))\n'
        'if sys.argv[2]=="success":\n'
        '    request=json.loads(sys.stdin.read())\n'
        '    print(json.dumps({"protocol_version":"1","case_id":request["case_id"],"operation":"eval","status":"ok","result":{"stdout":"done\\n","stderr":"","exit_code":0},"unsupported_reason":None}),flush=True)\n'
        'else:\n'
        '    print("partial-timeout-output",flush=True)\n'
        '    threading.Event().wait(60)\n'
    )
    controller = r'''
import ctypes,json,os,signal,sys,threading,time
from pathlib import Path
from tools.spec_runner.protocol import build_request,run_adapter_request
import tools.spec_runner.protocol as protocol
assert ctypes.CDLL(None).prctl(36,1,0,0,0)==0
pid=None
try:
    if sys.argv[3]=='cancel':
        def cancel_when_child_ready(process,*args,**kwargs):
            assert process.stdout.readline()==b'partial-timeout-output\n'
            raise KeyboardInterrupt('diagnostic caller cancellation')
        protocol.subprocess.Popen.communicate=cancel_when_child_ready
    try:
        outcome=run_adapter_request([sys.executable,sys.argv[1],sys.argv[2],sys.argv[3]],
            build_request('cancel-descendant','eval',{'source':'1'}),timeout=1.0)
        fields={'kind':outcome.kind,'reason':outcome.reason,'stdout':outcome.stdout_raw,'result':outcome.result}
    except KeyboardInterrupt:
        fields={'kind':'caller_cancelled','reason':None,'stdout':'','result':None}
    pid=int(Path(sys.argv[2]).read_text())
    deadline=time.monotonic()+2.0
    # Bounded exit observation after cancellation; does not extend request time.
    while sys.argv[3]!='success' and time.monotonic()<deadline:
        path=Path('/proc')/str(pid)/'stat'
        if not path.exists() or path.read_text().rsplit(')',1)[1].split()[0]=='Z':break
        threading.Event().wait(.01)
    path=Path('/proc')/str(pid)/'stat'
    alive=path.exists() and path.read_text().rsplit(')',1)[1].split()[0]!='Z'
    print(json.dumps({**fields,'child_still_running':alive}))
finally:
    if pid is None and Path(sys.argv[2]).exists():
        pid=int(Path(sys.argv[2]).read_text())
    if pid is not None:
        try:os.kill(pid,signal.SIGKILL)
        except ProcessLookupError:pass
        try:os.waitpid(pid,0)
        except ChildProcessError:pass
'''
    completed = subprocess.run(
        [sys.executable, '-c', controller, str(adapter), str(pidfile), mode],
        capture_output=True, text=True, timeout=15,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    if mode == 'timeout':
        assert result['kind'] == 'timeout'
        assert result['reason'] == 'adapter exceeded 1.0s timeout'
        assert result['stdout'] == 'partial-timeout-output\n'
        assert result['child_still_running'] is False
    elif mode == 'cancel':
        assert result['kind'] == 'caller_cancelled'
        assert result['child_still_running'] is False
    else:
        assert result['kind'] == 'ok'
        assert result['result'] == {'stdout': 'done\n', 'stderr': '', 'exit_code': 0}
        assert result['child_still_running'] is True
