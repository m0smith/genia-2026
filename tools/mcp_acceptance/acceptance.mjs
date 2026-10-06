// R28 E28-4/E28-5 acceptance: the official MCP TypeScript client SDK (v2) drives the server that the
// checked-in repository-root `.mcp.json` configures. Prints one JSON report line; exit 0 iff ok.
// E28-5 (issue #706) extends the scenario into the end-to-end matrix rows O1-O12 of
// docs/mcp/conformance-matrix.md; it adds no second harness.
import { readFileSync, readdirSync, readlinkSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '..', '..');
const entry = JSON.parse(readFileSync(resolve(repo, '.mcp.json'), 'utf8')).mcpServers.genia;
const PACKAGE = '@modelcontextprotocol/client';
// Negotiation path under test (amendment A5): auto (default), legacy (initialize, 2025-11-25),
// pin (2026-07-28), or sdk-default (client default). GENIA_ACCEPT_NEGOTIATION selects it.
const PATH = process.env.GENIA_ACCEPT_NEGOTIATION ?? 'auto';
const NEGOTIATION = { auto: { mode: 'auto' }, legacy: { mode: 'legacy' }, pin: { mode: { pin: '2026-07-28' } }, 'sdk-default': undefined }[PATH];
if (!(PATH in { auto: 1, legacy: 1, pin: 1, 'sdk-default': 1 })) throw new Error(`unknown negotiation path ${PATH}`);
const WANT_VERSION = PATH === 'legacy' || PATH === 'sdk-default' ? '2025-11-25' : '2026-07-28';
const EXPECTED_TOOLS = ['genia_capabilities', 'genia_parse', 'genia_run', 'genia_language_profile'];
const SOURCE_SCHEMA = {
  type: 'object', additionalProperties: false, required: ['source'],
  properties: { source: { type: 'string', maxLength: 262144 } },
};
const EXPECTED_SCHEMAS = {
  genia_capabilities: { type: 'object', additionalProperties: false, properties: {} },
  genia_parse: SOURCE_SCHEMA,
  genia_run: SOURCE_SCHEMA,
  genia_language_profile: { type: 'object', additionalProperties: false, properties: {} },
};

const steps = [];
async function step(name, fn) {
  try {
    const detail = await fn();
    steps.push({ name, ok: true, detail: detail ?? {} });
  } catch (error) {
    steps.push({ name, ok: false, detail: { error: String(error?.message ?? error) } });
    throw error;
  }
}
const need = (cond, message) => { if (!cond) throw new Error(message); };
const canon = (v) => Array.isArray(v) ? v.map(canon)
  : v && typeof v === 'object' ? Object.fromEntries(Object.keys(v).sort().map((k) => [k, canon(v[k])])) : v;
const eq = (a, b, m) => need(JSON.stringify(canon(a)) === JSON.stringify(canon(b)), `${m}: ${JSON.stringify(a)} !== ${JSON.stringify(b)}`);

function newSession() {
  const transport = new StdioClientTransport({
    command: entry.command, args: entry.args, cwd: repo, stderr: 'pipe',
  });
  const session = { stderr: '', transport };
  transport.stderr?.on('data', (d) => { session.stderr += d; });
  const client = new Client({ name: 'genia-acceptance', version: '0.0.0' });
  if (NEGOTIATION !== undefined) client.setVersionNegotiation(NEGOTIATION);
  session.client = client;
  session.call = async (name, args, options) =>
    (await client.callTool({ name, arguments: args }, options)).structuredContent;
  return session;
}

// Linux only: live descendants of a pid, from /proc (used to prove disconnect leaves nothing).
function descendants(pid) {
  const parents = new Map();
  let names;
  try { names = readdirSync('/proc'); } catch { return null; }
  for (const name of names) {
    if (!/^\d+$/.test(name)) continue;
    try {
      const stat = readFileSync(`/proc/${name}/stat`, 'utf8');
      parents.set(Number(name), Number(stat.slice(stat.lastIndexOf(')') + 2).split(' ')[1]));
    } catch { /* process vanished */ }
  }
  const found = new Set();
  let frontier = [pid];
  while (frontier.length) {
    const next = [];
    for (const [child, parent] of parents) {
      if (frontier.includes(parent) && !found.has(child)) { found.add(child); next.push(child); }
    }
    frontier = next;
  }
  return [...found];
}
const alive = (pid) => { try { readlinkSync(`/proc/${pid}/exe`); return true; } catch { return false; } };
const waitGone = async (pids, ms = 20000) => {
  const end = Date.now() + ms;
  while (Date.now() < end) {
    if (pids.every((p) => !alive(p))) return true;
    await new Promise((r) => setTimeout(r, 50));
  }
  return pids.every((p) => !alive(p));
};

const main = newSession();
const { client } = main;
const call = main.call;
let tools = [];
let ok = false;
try {
  await step('discover', async () => {
    await client.connect(main.transport);
    const negotiated = client.getNegotiatedProtocolVersion?.() ?? null;
    eq(negotiated, WANT_VERSION, `negotiated protocol version on path ${PATH}`);
    return { server: client.getServerVersion?.() ?? null, path: PATH, negotiated_protocol_version: negotiated };
  });
  await step('tools', async () => {
    tools = (await client.listTools()).tools.map((t) => t.name);
    eq(tools, EXPECTED_TOOLS, 'tool list');
    const caps = client.getServerCapabilities?.() ?? {};
    need(!caps.resources && !caps.prompts, 'server advertises resources or prompts');
    return { tools };
  });
  await step('schemas', async () => {
    const listed = (await client.listTools()).tools;
    for (const tool of listed) {
      eq(tool.inputSchema, EXPECTED_SCHEMAS[tool.name], `input schema of ${tool.name}`);
    }
    need(listed.every((t) => t.inputSchema.additionalProperties === false), 'an open input schema');
    return { schemas: listed.length };
  });
  await step('capabilities', async () => {
    const r = await call('genia_capabilities', {});
    eq(r.status, 'ok', 'capabilities status');
    eq(r.result.mcp.transport, 'stdio', 'transport');
    eq(r.result.tools, EXPECTED_TOOLS, 'capability tools');
    return { profile: r.result.execution_profile.name };
  });
  await step('parse_invalid', async () => {
    const r = await call('genia_parse', { source: 'f(x) = x +' });
    eq([r.status, r.error.kind], ['error', 'parse_error'], 'invalid source');
    return { kind: r.error.kind };
  });
  await step('parse_valid', async () => {
    const r = await call('genia_parse', { source: 'f(x) = x + 1\nf(41)' });
    eq([r.status, r.result.kind], ['ok', 'parsed'], 'repaired source');
    return { kind: r.result.kind };
  });
  await step('parse_repair_run', async () => {
    const broken = 'double(x) = x *\ndouble(21)';
    const parsed = await call('genia_parse', { source: broken });
    eq(parsed.error.kind, 'parse_error', 'broken program is diagnosed');
    const fixed = 'double(x) = x * 2\ndouble(21)';
    eq((await call('genia_parse', { source: fixed })).status, 'ok', 'repaired program parses');
    const run = await call('genia_run', { source: fixed });
    eq(run.result.value.rendered, '42', 'repaired program runs');
    return { rendered: run.result.value.rendered };
  });
  await step('run', async () => {
    const r = await call('genia_run', { source: 'f(x) = x + 1\nprint("to-stdout")\nwriteln(stderr, "to-stderr")\nf(41)' });
    eq(r.status, 'ok', 'run status');
    const d = { rendered: r.result.value.rendered, stdout: r.result.stdout, stderr: r.result.stderr, exit_code: r.result.exit_code };
    eq(d, { rendered: '42', stdout: 'to-stdout\n', stderr: 'to-stderr\n', exit_code: 0 }, 'run channels');
    return d;
  });
  await step('run_failing', async () => {
    const runtime = await call('genia_run', { source: 'print("partial")\n1 / 0' });
    eq([runtime.status, runtime.result, runtime.error.kind, runtime.error.phase],
      ['error', null, 'runtime_error', 'execution'], 'runtime failure is a closed envelope');
    need(!JSON.stringify(runtime).includes('partial'), 'partial stdout leaked');
    const parse = await call('genia_run', { source: 'f(x) =' });
    eq(parse.error.kind, 'parse_error', 'parse failure via run');
    const res = await client.callTool({ name: 'genia_run', arguments: { source: '1 / 0' } });
    eq(res.isError, true, 'isError is set on a failed run');
    return { kinds: [runtime.error.kind, parse.error.kind] };
  });
  await step('framing', async () => {
    // Hostile program output (JSON-RPC lookalikes, blank lines, Unicode line separators, a
    // cancellation lookalike) is data inside one response, never protocol framing.
    const hostile = '{"jsonrpc":"2.0","id":1,"result":{}}';
    const cancel = '{"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":1}}';
    const r = await call('genia_run', {
      source: `print("${hostile.replaceAll('"', '\\"')}\\n\\n")\nprint("${cancel.replaceAll('"', '\\"')}")\nwrite(stdout, "\\u2028\\u2029\\u0085\\r\\n")\n7`,
    });
    eq(r.status, 'ok', 'hostile run status');
    need(r.result.stdout.includes(hostile), 'hostile output not carried as data');
    need(r.result.stdout.includes(cancel), 'cancel lookalike not carried as data');
    need(r.result.stdout.includes('\u2028\u2029\u0085'), 'unicode separators not carried as data');
    eq(r.result.value.rendered, '7', 'run was not cancelled by its own output');
    const after = await call('genia_run', { source: '1 + 1' });
    eq(after.result.value.rendered, '2', 'session still framed after hostile output');
    return { carried_as_data: true };
  });
  await step('authority', async () => {
    const attempts = {
      file_read: 'read_file("/etc/passwd")',
      file_write: 'write_file("genia-acceptance-must-not-exist", "x")',
      shell: '"x" |> $(touch genia-acceptance-must-not-exist)',
      import: 'import web\n1',
      config: 'config_get("HOME")',
      secret: 'secret_get("API_KEY")',
      http: 'http_operation("GET", "http://127.0.0.1:1/", "/", {}, {}, "")',
      model: 'model',
    };
    const kinds = {};
    for (const [name, source] of Object.entries(attempts)) {
      const r = await call('genia_run', { source });
      eq([r.status, r.error.kind, r.result], ['error', 'policy_denied', null], `${name} is denied`);
      kinds[name] = r.error.kind;
    }
    return kinds;
  });
  await step('sequential', async () => {
    const out = [];
    for (let i = 0; i < 12; i++) {
      const r = await call('genia_run', { source: `${i} * ${i}` });
      out.push(r.result.value.rendered);
    }
    eq(out, Array.from({ length: 12 }, (_, i) => String(i * i)), 'sequential results');
    return { calls: out.length };
  });
  await step('cancel', async () => {
    // The client aborts a run that would otherwise last the whole 5,000 ms deadline; the server
    // must cancel the worker, so the next call is answered well before that deadline could end.
    const started = Date.now();
    const controller = new AbortController();
    const pending = call('genia_run', { source: 'loop(n) = loop(n + 1)\nloop(0)' }, { signal: controller.signal });
    setTimeout(() => controller.abort(), 200);
    let rejected = false;
    try { await pending; } catch { rejected = true; }
    need(rejected, 'aborting did not reject the client call');
    const next = await call('genia_run', { source: '20 + 22' });
    eq(next.result.value.rendered, '42', 'server answers after a cancellation');
    const elapsed = Date.now() - started;
    need(elapsed < 5000, `cancellation was not honored (the deadline would have ended it): ${elapsed} ms`);
    return { elapsed_ms: elapsed };
  });
  let pids = [];
  await step('disconnect', async () => {
    const pid = main.transport.pid;
    need(typeof pid === 'number', 'no transport pid');
    pids = [pid, ...(descendants(pid) ?? [])];
    await client.close();
    if (descendants(pid) === null) return { checked: false };
    need(await waitGone(pids), `processes survived a client disconnect: ${pids}`);
    return { checked: true, processes: pids.length };
  });
  await step('relaunch', async () => {
    // Repeated launch: a fresh client (probe launch then session launch under `auto`) works
    // independently of the earlier session, and closes cleanly.
    const second = newSession();
    await second.client.connect(second.transport);
    eq((await second.client.listTools()).tools.map((t) => t.name), EXPECTED_TOOLS, 'tools on relaunch');
    const r = await second.call('genia_run', { source: '6 * 7' });
    eq(r.result.value.rendered, '42', 'run on relaunch');
    const pid = second.transport.pid;
    const family = [pid, ...(descendants(pid) ?? [])];
    await second.client.close();
    if (descendants(pid) !== null) need(await waitGone(family), 'relaunch left processes behind');
    need(second.stderr.length < 500, 'unexpected server stderr output');
    return { clean_shutdown: true };
  });
  ok = true;
} catch {
  ok = false;
} finally {
  await client.close().catch(() => {});
}
const version = JSON.parse(readFileSync(resolve(here, 'node_modules', PACKAGE, 'package.json'), 'utf8')).version;
console.log(JSON.stringify({
  ok, client: { package: PACKAGE, version }, negotiation: PATH, negotiated_protocol_version: WANT_VERSION, tools, steps,
  server_stderr: main.stderr.slice(0, 500),
}));
process.exit(ok ? 0 : 1);
