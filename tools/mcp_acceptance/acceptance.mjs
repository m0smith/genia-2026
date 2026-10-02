// R28 E28-4 acceptance: the official MCP TypeScript client SDK (v2) drives the server that the
// checked-in repository-root `.mcp.json` configures. Prints one JSON report line; exit 0 iff ok.
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '..', '..');
const entry = JSON.parse(readFileSync(resolve(repo, '.mcp.json'), 'utf8')).mcpServers.genia;
const PACKAGE = '@modelcontextprotocol/client';
const NEGOTIATION = 'auto'; // the stateless server has no `initialize`; legacy mode cannot connect
const EXPECTED_TOOLS = ['genia_capabilities', 'genia_parse', 'genia_run'];

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
const eq = (a, b, m) => need(JSON.stringify(a) === JSON.stringify(b), `${m}: ${JSON.stringify(a)} !== ${JSON.stringify(b)}`);

const transport = new StdioClientTransport({
  command: entry.command, args: entry.args, cwd: repo, stderr: 'pipe',
});
let stderr = '';
transport.stderr?.on('data', (d) => { stderr += d; });
const client = new Client({ name: 'genia-acceptance', version: '0.0.0' });
client.setVersionNegotiation({ mode: NEGOTIATION });
const call = async (name, args) => (await client.callTool({ name, arguments: args })).structuredContent;

let tools = [];
let ok = false;
try {
  await step('discover', async () => {
    await client.connect(transport);
    return { server: client.getServerVersion?.() ?? null };
  });
  await step('tools', async () => {
    tools = (await client.listTools()).tools.map((t) => t.name);
    eq(tools, EXPECTED_TOOLS, 'tool list');
    const caps = client.getServerCapabilities?.() ?? {};
    need(!caps.resources && !caps.prompts, 'server advertises resources or prompts');
    return { tools };
  });
  await step('capabilities', async () => {
    const r = await call('genia_capabilities', {});
    eq(r.status, 'ok', 'capabilities status');
    eq(r.result.mcp.transport, 'stdio', 'transport');
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
  await step('run', async () => {
    const r = await call('genia_run', { source: 'f(x) = x + 1\nprint("to-stdout")\nwriteln(stderr, "to-stderr")\nf(41)' });
    eq(r.status, 'ok', 'run status');
    const d = { rendered: r.result.value.rendered, stdout: r.result.stdout, stderr: r.result.stderr, exit_code: r.result.exit_code };
    eq(d, { rendered: '42', stdout: 'to-stdout\n', stderr: 'to-stderr\n', exit_code: 0 }, 'run channels');
    return d;
  });
  await step('framing', async () => {
    // Hostile program output (JSON-RPC lookalikes, blank lines) is data inside one response.
    const hostile = '{"jsonrpc":"2.0","id":1,"result":{}}';
    const r = await call('genia_run', { source: `print("${hostile.replaceAll('"', '\\"')}\\n\\n")\n7` });
    eq(r.status, 'ok', 'hostile run status');
    need(r.result.stdout.includes(hostile), 'hostile output not carried as data');
    const after = await call('genia_run', { source: '1 + 1' });
    eq(after.result.value.rendered, '2', 'session still framed after hostile output');
    return { carried_as_data: true };
  });
  await step('authority', async () => {
    const r = await call('genia_run', { source: 'read_file("/etc/passwd")' });
    eq([r.status, r.error.kind], ['error', 'policy_denied'], 'file read');
    return { kind: r.error.kind };
  });
  ok = true;
} catch {
  ok = false;
} finally {
  await client.close().catch(() => {});
}
const version = JSON.parse(readFileSync(resolve(here, 'node_modules', PACKAGE, 'package.json'), 'utf8')).version;
console.log(JSON.stringify({
  ok, client: { package: PACKAGE, version }, negotiation: NEGOTIATION, tools, steps,
  server_stderr: stderr.slice(0, 500),
}));
process.exit(ok ? 0 : 1);
