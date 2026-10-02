// R28 E28-5 (ledger R28-H36): what the official TypeScript client does with each version-negotiation
// mode against the configured server. Evidence only; the server is not changed by this script.
// Prints one JSON report line. Exit 0 iff the recorded expectation holds (legacy rejected with
// "Method not found"; `auto` and a pinned 2026-07-28 connect and list exactly the three tools).
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '..', '..');
const entry = JSON.parse(readFileSync(resolve(repo, '.mcp.json'), 'utf8')).mcpServers.genia;

async function attempt(label, negotiation) {
  const transport = new StdioClientTransport({ command: entry.command, args: entry.args, cwd: repo, stderr: 'pipe' });
  const client = new Client({ name: 'genia-negotiation', version: '0.0.0' });
  if (negotiation !== undefined) client.setVersionNegotiation(negotiation);
  const report = { label, negotiation: negotiation ?? 'sdk-default', connected: false };
  try {
    await client.connect(transport);
    report.connected = true;
    report.tools = (await client.listTools()).tools.map((t) => t.name);
  } catch (error) {
    report.error = String(error?.message ?? error).slice(0, 200);
  } finally {
    await client.close().catch(() => {});
  }
  return report;
}

const results = [
  await attempt('sdk-default', undefined),
  await attempt('legacy', { mode: 'legacy' }),
  await attempt('auto', { mode: 'auto' }),
  await attempt('pin', { mode: { pin: '2026-07-28' } }),
];
const by = Object.fromEntries(results.map((r) => [r.label, r]));
const tools = ['genia_capabilities', 'genia_parse', 'genia_run'];
const ok =
  !by['sdk-default'].connected && /Method not found/.test(by['sdk-default'].error ?? '') &&
  !by.legacy.connected && /Method not found/.test(by.legacy.error ?? '') &&
  by.auto.connected && JSON.stringify(by.auto.tools) === JSON.stringify(tools) &&
  by.pin.connected && JSON.stringify(by.pin.tools) === JSON.stringify(tools);
const version = JSON.parse(readFileSync(resolve(here, 'node_modules', '@modelcontextprotocol/client', 'package.json'), 'utf8')).version;
console.log(JSON.stringify({ ok, client_version: version, results }));
process.exit(ok ? 0 : 1);
