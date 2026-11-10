"""Host-local harness interpreter selection through uv and the official SDK; no Genia semantics."""

import json
import os
import subprocess
import sys

from tests.fixtures.r28_mcp_helpers import client_environment, configured_command, ACCEPTANCE_HARNESS_DIR
from tests.unit import test_r28_mcp_official_client as official


PROBE = """import json, os, sys
print(json.dumps({'jsonrpc': '2.0', 'method': 'probe', 'params': {
    'executable': sys.executable,
    'downloads': os.environ.get('UV_PYTHON_DOWNLOADS'),
    'secret': os.environ.get('GENIA_TEST_SECRET'),
}}), flush=True)
"""


def _mismatched_pin(tmp_path):
    """Request a different minor version while preserving the configured uv argv shape."""
    (tmp_path / '.python-version').write_text('3.10' if sys.version_info[:2] != (3, 10) else '3.12')
    script = tmp_path / 'hosts/python/mcp_launch.py'
    script.parent.mkdir(parents=True)
    script.write_text(PROBE)
    return tmp_path


def _assert_selected(report):
    """The selected executable must be this pytest's interpreter, with downloads and secrets off."""
    assert os.path.samefile(report['executable'], sys.executable)
    assert report['downloads'] == 'never'
    assert report['secret'] is None


def test_python_client_selects_active_interpreter_with_a_mismatched_pin(tmp_path, monkeypatch):
    monkeypatch.setenv('UV_PYTHON', '/not-the-active-python')
    monkeypatch.setenv('GENIA_TEST_SECRET', 'must-not-reach-server')
    env = client_environment()
    assert env['UV_PYTHON'] == sys.executable
    done = subprocess.run(configured_command(), cwd=_mismatched_pin(tmp_path), env=env,
                          capture_output=True, text=True, timeout=20)
    assert done.returncode == 0, done.stderr
    _assert_selected(json.loads(done.stdout)['params'])


def test_official_sdk_selects_active_interpreter_with_a_mismatched_pin(tmp_path, monkeypatch):
    official._harness_ready()
    monkeypatch.setenv('UV_PYTHON', '/not-the-active-python')
    monkeypatch.setenv('GENIA_TEST_SECRET', 'must-not-reach-server')
    # Exercise the real SDK transport and the same environment helper used by both harnesses.
    script = """
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { clientEnvironment } from './client-environment.mjs';
const transport = new StdioClientTransport({
  command: 'uv', args: ['run', '--no-project', '--no-python-downloads', 'python', 'hosts/python/mcp_launch.py'],
  cwd: process.argv[1], env: clientEnvironment(), stderr: 'pipe',
});
const result = new Promise((resolve, reject) => {
  transport.onmessage = resolve;
  transport.onerror = reject;
  transport.onclose = () => reject(new Error('closed before probe'));
});
try { await transport.start(); console.log(JSON.stringify((await result).params)); }
finally { await transport.close(); }
"""
    done = subprocess.run(['node', '--input-type=module', '-e', script, str(_mismatched_pin(tmp_path))],
                          cwd=ACCEPTANCE_HARNESS_DIR, env=official._harness_environment(),
                          capture_output=True, text=True, timeout=20)
    assert done.returncode == 0, done.stderr
    _assert_selected(json.loads(done.stdout))
