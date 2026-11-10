// Test-only interpreter injection; the SDK retains its default safe environment allowlist.
/** Select the pytest interpreter for nested uv without forwarding ambient environment/secrets. */
export function clientEnvironment() {
  const python = process.env.GENIA_MCP_TEST_PYTHON;
  if (!python) throw new Error('GENIA_MCP_TEST_PYTHON must name the active test interpreter');
  return { UV_PYTHON: python, UV_PYTHON_DOWNLOADS: 'never' };
}
