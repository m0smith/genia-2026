"""Deterministic constrained Design A tests; synthetic APIs, no hosted execution."""

import base64
from copy import deepcopy
from datetime import timedelta
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from tools.issue_1250 import hosted_trust as trust, run
from tests.unit.test_issue_1250_hosted_trust import hosted, downloadable  # noqa: F401

PREFIX = '/repos/m0smith/genia-2026'
BASE = '9f96c6d9369bc29b87d6f63a97b3f7ce89bb7e05'


@pytest.fixture
def authority(hosted):
    """Model owner-enrolled numeric identities and complete source contributors."""
    expected, api, now = hosted
    policy = {'schema': 1, 'repository': trust.REPOSITORY, 'base_sha': BASE,
              'maintainers': [{'id': 10, 'login': 'maintainer'}],
              'reviewers': [{'id': 20, 'login': 'reviewer', 'enrolled_by': 10,
                             'enrolled_utc': '2026-11-01T00:00:00+00:00',
                             'authorization': 'https://github.com/m0smith/genia-2026/issues/1250#issuecomment-1',
                             'independence_attested': True}]}
    raw = json.dumps(policy).encode()
    api.values[PREFIX + '/contents/tools/issue_1250/reviewer-policy.json?ref=main'] = {
        'type': 'file', 'encoding': 'base64', 'content': base64.b64encode(raw).decode(),
        'sha': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}
    api.values[PREFIX + '/pulls/1318'] = {
        'base': {'sha': BASE, 'ref': 'issue-1250-acceptance-infrastructure', 'repo': {'full_name': trust.REPOSITORY}},
        'head': {'sha': expected['commit_sha'], 'repo': {'full_name': trust.REPOSITORY}}}
    api.values[PREFIX + '/actions/runs/55'] = {
        'id': 55, 'run_attempt': 1, 'event': 'workflow_dispatch',
        'head_sha': expected['commit_sha'], 'path': '.github/workflows/issue-1250-acceptance.yml',
        'repository': {'full_name': trust.REPOSITORY}, 'head_repository': {'full_name': trust.REPOSITORY},
        'actor': {'id': 10}, 'triggering_actor': {'id': 10}}
    api.values[PREFIX + f"/compare/{BASE}...{expected['commit_sha']}?per_page=100&page=1"] = {
        'status': 'ahead', 'ahead_by': 1, 'behind_by': 0, 'total_commits': 1,
        'base_commit': {'sha': BASE}, 'merge_base_commit': {'sha': BASE},
        'commits': [{'sha': expected['commit_sha'], 'author': {'id': 30}, 'committer': {'id': 31}}]}
    for suffix in ('', '/attempts/1'):
        metadata = api.values[PREFIX + '/actions/runs/41' + suffix]
        metadata['actor']['id'] = 40
        metadata['triggering_actor']['id'] = 41
    return expected, api, now, hashlib.sha256(raw).hexdigest()


def test_policy_is_from_main_and_requires_dispatcher(authority):
    expected, api, _, digest = authority
    policy = trust.verify_authority(api, digest, 55, expected['commit_sha'])
    assert policy.reviewer_ids == frozenset({20})
    assert {10, 30, 31}.issubset(policy.excluded_ids)
    assert any(p.endswith('reviewer-policy.json?ref=main') for p in api.calls)


@pytest.mark.parametrize('change', ['digest', 'encoding', 'blob', 'unknown-dispatcher', 'rerun',
                                  'wrong-source', 'wrong-workflow', 'wrong-base', 'truncated',
                                  'ambiguous-author', 'ambiguous-committer', 'diverged', 'malformed'])
def test_policy_and_contributors_fail_closed(authority, change):
    expected, api, _, digest = authority
    dispatch = api.values[PREFIX + '/actions/runs/55']
    compare = api.values[PREFIX + f"/compare/{BASE}...{expected['commit_sha']}?per_page=100&page=1"]
    if change == 'digest': digest = '0' * 64
    elif change == 'encoding': api.values[PREFIX + '/contents/tools/issue_1250/reviewer-policy.json?ref=main']['encoding'] = 'utf-8'
    elif change == 'blob': api.values[PREFIX + '/contents/tools/issue_1250/reviewer-policy.json?ref=main']['sha'] = '0' * 40
    elif change == 'unknown-dispatcher': dispatch['triggering_actor']['id'] = 999
    elif change == 'rerun': dispatch['run_attempt'] = 2
    elif change == 'wrong-source': dispatch['head_sha'] = '0' * 40
    elif change == 'wrong-workflow': dispatch['path'] = 'other.yml'
    elif change == 'wrong-base': api.values[PREFIX + '/pulls/1318']['base']['sha'] = '0' * 40
    elif change == 'truncated': compare['total_commits'] = 2
    elif change == 'ambiguous-author': compare['commits'][0]['author'] = None
    elif change == 'ambiguous-committer': compare['commits'][0]['committer'] = None
    elif change == 'diverged': compare['behind_by'] = 1
    elif change == 'malformed': api.values[PREFIX + '/actions/runs/55'] = []
    with pytest.raises(RuntimeError, match='authority rejected'):
        trust.verify_authority(api, digest, 55, expected['commit_sha'])


def receipt_fixture(expected, api, now):
    """Bind a synthetic receipt to a synthetic genuine-review-shaped API response."""
    receipt = {**expected, 'status': 'APPROVED', 'scope': 'dependency-baseline-activation',
               'reviewer': 20, 'expires_utc': (now + timedelta(hours=1)).isoformat(),
               'review': {'pull_number': 1318, 'id': 88}}
    api.values[PREFIX + '/pulls/1318/reviews/88'] = {
        'id': 88, 'state': 'APPROVED', 'commit_id': expected['commit_sha'],
        'user': {'id': 20, 'login': 'renamed-reviewer'}, 'submitted_at': now.isoformat(),
        'body': 'ISSUE1250-APPROVAL sha256:' + trust.receipt_digest(receipt)}
    return receipt


def test_numeric_review_approval(authority):
    expected, api, now, digest = authority
    policy = trust.verify_authority(api, digest, 55, expected['commit_sha'])
    receipt = receipt_fixture(expected, api, now)
    assert trust.verify_receipt(api, receipt, expected, policy, now=now)['reviewer'] == 20


@pytest.mark.parametrize('change', ['wrong-id', 'author', 'committer', 'dispatcher', 'collector',
                                  'triggering-collector', 'commented', 'dismissed', 'marker',
                                  'commit', 'pending', 'expired', 'missing', 'login-allowlist'])
def test_numeric_review_rejections(authority, change):
    expected, api, now, digest = authority
    receipt = receipt_fixture(expected, api, now)
    policy = trust.verify_authority(api, digest, 55, expected['commit_sha'])
    review = api.values[PREFIX + '/pulls/1318/reviews/88']
    if change == 'wrong-id': review['user']['id'] = 21
    elif change in {'author', 'committer', 'dispatcher', 'collector', 'triggering-collector'}:
        identity = {'author': 30, 'committer': 31, 'dispatcher': 10, 'collector': 40, 'triggering-collector': 41}[change]
        receipt['reviewer'] = review['user']['id'] = identity
        # Even a policy containing an excluded identity must reject it.
        from dataclasses import replace
        policy = replace(policy, reviewer_ids=frozenset({identity}))
        review['body'] = 'ISSUE1250-APPROVAL sha256:' + trust.receipt_digest(receipt)
    elif change == 'commented': review['state'] = 'COMMENTED'
    elif change == 'dismissed': review['state'] = 'DISMISSED'
    elif change == 'marker': review['body'] = 'ISSUE1250-APPROVAL sha256:' + '0' * 64
    elif change == 'commit': review['commit_id'] = '0' * 40
    elif change == 'pending': receipt['status'] = 'PENDING'
    elif change == 'expired': receipt['expires_utc'] = (now - timedelta(seconds=1)).isoformat()
    elif change == 'missing': receipt = None
    elif change == 'login-allowlist': policy = {'renamed-reviewer'}
    with pytest.raises(RuntimeError, match='receipt rejected'):
        trust.verify_receipt(api, receipt, expected, policy, now=now)


@pytest.mark.parametrize('value', ['', '\n', 'bad token\n', 'x\ny\n', 'x' * 8193])
def test_missing_or_malformed_stdin_token(value):
    with pytest.raises(RuntimeError, match='stdin credential'):
        run.read_token(io.StringIO(value))


def test_token_is_read_once_and_stdin_is_closed():
    stream = io.StringIO('github-token-canary\n')
    assert run.read_token(stream) == 'github-token-canary'
    assert stream.closed


@pytest.mark.parametrize('binary', ['python', 'uv'])
def test_executable_hash_mismatch(tmp_path, monkeypatch, binary):
    python, uv = tmp_path / 'python', tmp_path / 'uv'
    python.write_bytes(b'python')
    uv.write_bytes(b'uv')
    monkeypatch.setattr(run.sys, 'executable', str(python))
    monkeypatch.setattr(run.shutil, 'which', lambda name: str(uv))
    record = {'environment': {'python_sha256': hashlib.sha256(b'python').hexdigest(),
                              'uv_sha256': hashlib.sha256(b'uv').hexdigest()}}
    run.verify_toolchain(record)
    (python if binary == 'python' else uv).write_bytes(b'changed')
    with pytest.raises(RuntimeError, match='executable hash'):
        run.verify_toolchain(record)


def test_subprocess_canary_has_no_token_env_argv_files_or_fds(tmp_path, monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'credential-canary')
    monkeypatch.setenv('GH_TOKEN', 'credential-canary')
    monkeypatch.setenv('UNRELATED_SECRET', 'credential-canary')
    read_fd, write_fd = os.pipe()
    os.set_inheritable(read_fd, True)
    os.write(write_fd, b'credential-canary')
    try:
        script = "import os,sys,json; print(json.dumps({'env':dict(os.environ),'argv':sys.argv,'fds':os.listdir('/proc/self/fd'),'stdin':sys.stdin.read()}))"
        value = json.loads(run.command([sys.executable, '-c', script], tmp_path, tmp_path, 'canary'))
        assert all('credential-canary' not in str(v) for v in value.values())
        assert value['stdin'] == ''
        assert str(read_fd) not in value['fds'] or int(read_fd) <= 3
        assert all(b'credential-canary' not in p.read_bytes() for p in tmp_path.iterdir())
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_forged_capability_cannot_provision(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(run, 'provision_locked', lambda *a, **k: calls.append(a))
    for capability in (None, {}, {'verified': True}, object()):
        with pytest.raises(RuntimeError):
            run.provision(tmp_path, 'a' * 40, tmp_path, 'blocked', authorization=capability)
    assert calls == [] and run.APPROVED_DEPENDENCIES is None


def test_verification_failure_precedes_all_subject_activity(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(run.os, 'getpid', lambda: 1)
    def reject(*a, **k):
        raise RuntimeError('verification deliberately failed')
    monkeypatch.setattr(run, 'authorize', reject)
    monkeypatch.setattr(run, 'command', lambda *a, **k: calls.append(a))
    monkeypatch.setattr(run, 'git', lambda *a: calls.append(a))
    with pytest.raises(RuntimeError, match='verification deliberately failed'):
        run.main(['smoke', '--baseline', str(tmp_path/'baseline'), '--work', str(tmp_path/'work')])
    assert calls == []
    assert json.loads((tmp_path/'work/evidence/authorization.json').read_text())['outcome'] == 'BLOCKED'


@pytest.mark.parametrize('code', [403, 429, 'malformed'])
def test_api_errors_are_redacted_and_closed(code):
    client = trust.GitHubReadOnly('credential-canary')
    class Broken:
        def open(self, *a, **k):
            raise RuntimeError(f'{code}: credential-canary')
    client._opener = Broken()
    with pytest.raises(RuntimeError, match='metadata read failed') as caught:
        client.json(PREFIX)
    assert 'credential-canary' not in str(caught.value)
    client.close()
    assert client._token is None and client._opener is None
    with pytest.raises(RuntimeError):
        client.json(PREFIX)


def test_workflow_constrained_permissions_pins_and_stdin():
    workflow = yaml.load((Path(run.HERE).parents[1]/'.github/workflows/issue-1250-acceptance.yml').read_text(), Loader=yaml.BaseLoader)
    permissions = {'contents': 'read', 'actions': 'read', 'pull-requests': 'read'}
    assert workflow['permissions'] == permissions
    for job in workflow['jobs'].values():
        assert job['permissions'] == permissions
        assert not any(s['name'].startswith('Checkout unchanged main') or s['name'].startswith('Checkout frozen candidate') for s in job['steps'])
        for step in job['steps']:
            if 'uses' in step:
                assert len(step['uses'].split('@')[1].split()[0]) == 40
        gate = next(s for s in job['steps'] if s.get('id') == 'gate')
        assert gate['env']['CONTROLLER_TOKEN'] == '${{ github.token }}'
        assert 'printf' in gate['run'] and '| /usr/bin/sudo' in gate['run']
        assert '--setenv="CONTROLLER_TOKEN' not in gate['run']
        assert 'python -m tools.issue_1250.hosted_collection bootstrap-uv' in str(job)
