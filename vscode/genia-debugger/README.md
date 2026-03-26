# Genia Debugger (VS Code)

This is the first minimal VS Code extension for the Genia project. It adds a `genia` debugger that bridges VS Code DAP requests to the Genia runtime's JSON-over-stdio debug transport.

## What this extension supports today

- Launching Genia programs in debug mode (`request: "launch"`)
- Line breakpoints
- Continue / step in / step over / step out
- Stack trace
- Local and global scopes
- Variable inspection (name / value / type)

## What this extension does **not** support yet

- Attach mode
- Conditional breakpoints
- Exception breakpoints
- Watch expressions
- Data breakpoints
- Debug console REPL integration
- Inline values
- Any language features (syntax highlighting, snippets, LSP, hover, completion)

## Runtime assumptions

By default, the adapter launches:

```bash
python3 -m genia.interpreter --debug-stdio <program>
```

You can override the executable and args with:

- `runtimeExecutable`
- `runtimeArgs`

When `runtimeArgs` is not provided, it defaults to `['-m', 'genia.interpreter']`.

## Launch configuration

Minimal example (`.vscode/launch.json`):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "genia",
      "request": "launch",
      "name": "Launch Genia File",
      "program": "${file}",
      "cwd": "${workspaceFolder}",
      "stopOnEntry": true
    }
  ]
}
```

Optional fields:

- `cwd`
- `runtimeExecutable`
- `runtimeArgs`
- `stopOnEntry`

## Run in Extension Development Host

1. `cd vscode/genia-debugger`
2. `npm install`
3. `npm run build`
4. Open this folder in VS Code.
5. Press `F5` with the **Run Genia Debugger Extension** launch config.
6. In the Extension Development Host window, create/use a `.genia` file and run the **Launch Genia File** debug configuration.

## Architecture (minimal)

- `src/extension.ts`: registers a debug adapter descriptor factory for debugger type `genia`.
- `src/geniaDebugAdapter.ts`: standalone debug adapter process using `@vscode/debugadapter`.
- Adapter launches Genia runtime as a child process and exchanges JSON lines over stdio.
- DAP requests are translated to Genia commands; Genia events/responses are translated back to DAP events/responses.

## Next logical milestone

Add robust protocol correlation IDs and richer variable expansion (nested values with non-zero variable references), then add attach mode.
