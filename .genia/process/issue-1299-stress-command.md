# #1299 bounded stress command

Private audit orchestration uses the existing R16 request/response transport;
it adds no runner/protocol/registry to the product. Run from the checked-out
candidate with PYTHONPATH pointing at repository and src, through uv run.
Arguments are YAML path, adapter executable, fixed count and output JSON path.
Python adapter executable is a shell wrapper invoking the project Python with
`-m hosts.python.protocol_adapter`. It preserves inherited PYTHONPATH.

```python
"""Bounded once-per-request R16 stress evidence; never retries or reclassifies failures."""
import concurrent.futures
from collections import Counter
import json
from pathlib import Path
import sys
import yaml
from tools.spec_runner.protocol import build_request, run_adapter_request

case=yaml.safe_load(Path(sys.argv[1]).read_text())
command=[sys.argv[2]]
count=int(sys.argv[3]); output=Path(sys.argv[4])
request=build_request(case['name'],'eval',case['input'])
def invoke(index):
    result=run_adapter_request(command,request,timeout=10,cwd=str(Path.cwd()))
    classification=('pass' if result.result==case['expected'] else 'fail') if result.kind=='ok' else result.kind
    return {'index':index,'classification':classification,'kind':result.kind,'result':result.result,'reason':result.reason}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    records=list(executor.map(invoke,range(count)))
payload={'command':command,'requests':count,'max_concurrent':8,'counts':dict(Counter(x['classification'] for x in records)),'records':records}
output.write_text(json.dumps(payload,indent=2)+'\n')
print(json.dumps({k:v for k,v in payload.items() if k!='records'}))
```

Final batches use request_timeout_seconds10; max8concurrent; no retry, sleep,
capability gating change or classification relaxation. Zero failure classes
means every result exactly equalled the existing expected dictionary.
The30s initial support batches are retained separately and excluded from final
acceptance. Test Event/join safety bounds5s are not language scheduling promises.
