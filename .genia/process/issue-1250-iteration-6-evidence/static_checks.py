"""Retain bounded static source/evidence/workflow checks without executing run blocks."""
from pathlib import Path
import ast
import hashlib
import json
import subprocess
import yaml
from tools.issue_1250 import approval_validation, run

ROOT=Path.cwd()
BASE='39747f64989336fa919655e0239488a21a5a7dee'
OUT=ROOT/'.genia/process/issue-1250-iteration-6-evidence'
def digest(data):
    """Hash exact artifact bytes without normalization."""
    return hashlib.sha256(data).hexdigest()
def write(name,value):
    """Retain a deterministic local audit record."""
    (OUT/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],text=True).splitlines()
protected=[]
for path in paths:
    if (path.startswith('tools/issue_1250/dependencies/') or
        path in {'tools/issue_1250/activation.proposed.patch','tools/issue_1250/registration.json',
                 'tools/issue_1250/registration-proposal.json','tools/issue_1250/hosted-receipt.pending.json',
                 'tools/issue_1250/approved-qualification.json','tools/issue_1250/hosted-policy.json',
                 'AGENTS.md','GENIA_STATE.md','GENIA_RULES.md','GENIA_REPL_README.md','README.md','pyproject.toml'} or
        (path.startswith('.genia/process/issue-1250') and not path.endswith('.md')) or
        path.startswith(('src/','spec/','hosts/','tests/fixtures/')) or
        (path.startswith('tests/') and 'test_issue_1250' not in path)):
        old=subprocess.check_output(['git','show',BASE+':'+path])
        current=(ROOT/path).read_bytes()
        assert current==old,path
        protected.append({'path':path,'sha256':digest(current)})
assert run.APPROVED_DEPENDENCIES is None
assert len(run.REGISTRATION['original'])==22
assert run.LOCK=='27ca5a9328ba8641ce18078782c7edecdc8a753aa6b4fd3ca57932a66d49f291'
assert json.loads((run.HERE/'reviewer-policy.json').read_text())['reviewers']==[]
sources=approval_validation.sources()
assert 'tools/issue_1250/reviewer-policy.json' in sources
assert sources['tools/issue_1250/run.py']==digest((run.HERE/'run.py').read_bytes())
write('source-fingerprints.json',sources)
write('preserved-inputs.json',{'base':BASE,'count':len(protected),'sha256':{v['path']:v['sha256'] for v in protected},
    'sentinel':None,'original_nodes':22,'historical_lock':run.LOCK,'superseded_patch_unapplied':True})
blocks=0
for workflow in sorted((ROOT/'.github/workflows').glob('issue-1250*.yml')):
    data=yaml.load(workflow.read_text(),Loader=yaml.BaseLoader)
    assert set(data['on'])=={'workflow_dispatch'}
    for job in data['jobs'].values():
        for step in job['steps']:
            if 'run' in step:
                subprocess.run(['bash','-n'],input=step['run'],text=True,check=True)
                blocks+=1
            if 'uses' in step:
                pin=step['uses'].split('@')[1]
                assert len(pin)==40 and all(c in '0123456789abcdef' for c in pin)
for path in [*Path('tools/issue_1250').glob('*.py'),*Path('tests/unit').glob('test_issue_1250*.py')]:
    ast.parse(path.read_text())
print(f'PASS: {len(protected)} protected inputs byte-identical; {len(sources)} source fingerprints; {blocks} bash blocks syntax-checked without execution; sentinel None; original 22 preserved')
