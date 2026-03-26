# Genia Debugger (VS Code)

This VS Code extension provides two things for Genia:

- A minimal `genia` debugger that bridges VS Code DAP requests to the Genia runtime's JSON-over-stdio debug transport.
- Basic language support for `.genia` files.

## Language support for `.genia`

The extension now contributes a `genia` language with:

- Automatic file recognition for `*.genia`
- Syntax highlighting (TextMate grammar)
- Bracket matching for `()`, `[]`, `{}`
- Line comments with `#`
- Basic indentation behavior around `{` and `}`

This is intentionally minimal and does **not** include LSP features (autocomplete, hover, go-to-definition, rename, semantic analysis, formatting, linting, etc.).

## Debugging support

## What this extension supports today

- Launching Genia programs in debug mode (`request: "launch"`)
- Line breakpoints
- Continue / step in / step over / step out
- Stack trace
- Local and global scopes
- Variable inspection (name / value / type)
- Launching from `.genia` files via the `genia` debugger configuration

## What this extension does **not** support yet

- Attach mode
- Conditional breakpoints
- Exception breakpoints
- Watch expressions
- Data breakpoints
- Debug console REPL integration
- Inline values
- Language server features (autocomplete, hover, go-to-definition, etc.)

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

## Run in Extension Development Host (dev mode)

1. `cd vscode/genia-debugger`
2. `npm install`
3. `npm run build`
4. Open this folder in VS Code.
5. Press `F5` with the **Run Genia Debugger Extension** launch config.
6. In the Extension Development Host window, open `example.genia` (or any `.genia` file) to validate highlighting/comments/brackets.
7. Run the **Launch Genia File** debug configuration.

## Architecture (minimal)

- `src/extension.ts`: registers a debug adapter descriptor factory for debugger type `genia`.
- `src/geniaDebugAdapter.ts`: standalone debug adapter process using `@vscode/debugadapter`.
- `language-configuration.json`: basic editing behavior (comments, brackets, pairs, indentation).
- `syntaxes/genia.tmLanguage.json`: regex-based TextMate highlighting rules.

## Next logical milestone

Add robust protocol correlation IDs and richer variable expansion (nested values with non-zero variable references), then add attach mode.
