# === GENIA CONTRACT ===

CHANGE NAME: issue #283 seq-decide-boundary
CHANGE SLUG: issue-283-seq-decide-boundary
ISSUE: #283 — Seq: Decide stdin compatibility boundary

Handoff directory:
`.genia/process/tmp/handoffs/issue-283-seq-decide-boundary/`

Output file:
`.genia/process/tmp/handoffs/issue-283-seq-decide-boundary/01-contract.md`

---

## 0. BRANCH CHECK

Expected branch:
`feature/issue-283-seq-decide-boundary`

Status:
- Contract written for the expected feature branch.
- Do not apply this contract on `main` directly.

---

## 1. PURPOSE

Define the Seq/stdin boundary for current Genia.

Decision:
- Raw `stdin` is **not** a direct Seq-compatible public value.
- `stdin` remains a host-backed input capability.
- `stdin` enters ordered Flow processing through the explicit bridge `lines(stdin)`.
- Pipe mode continues to inject `stdin |> lines` internally before applying the user-provided stage expression.

This contract affirms the current explicit bridge model instead of widening Seq compatibility.

---

## 2. SCOPE FROM PRE-FLIGHT

Included:
- Affirm the boundary between host input capability values and Seq-compatible public values.
- Clarify that implemented Seq-compatible public values are list and Flow only.
- Clarify that `stdin` is adapted into Flow through `lines`.
- Clarify pipe-mode interaction with this boundary.
- Define direct-stdin failure behavior for Seq-compatible terminal helpers.
- Define docs/tests needed to prevent #253-style over-promising.

Excluded:
- No raw `stdin` direct Seq compatibility.
- No public Seq runtime type, helper, syntax, or Core IR node.
- No Python generator or iterator exposure.
- No async streams.
- No scheduler semantics.
- No selective receive.
- No broad pipe-mode redesign.
- No implicit conversion of arbitrary values to Seq.
- No changes to `lines` behavior except documentation/diagnostic clarification if needed.
- No new parser syntax.
- No Core IR change.

---

## 3. BEHAVIOR

### 3.1 Seq-compatible public values

The implemented public Seq-compatible values are exactly:
- list
- Flow

Seq remains semantic terminology for ordered value production.
Seq is not:
- a public runtime value
- a type constructor
- a syntax form
- a helper function
- a Core IR node

### 3.2 `stdin`

`stdin` is a host-backed input capability.
It is not itself Seq-compatible.
It must be adapted through `lines` before it participates in Flow-style ordered processing.

Valid shape:
```genia
stdin |> lines |> collect
```

Valid effect shape:
```genia
stdin |> lines |> each(print) |> run
```

Invalid direct shapes:
```genia
stdin |> collect
stdin |> run
stdin |> each(print) |> run
```

### 3.3 `lines`

`lines(source)` remains the explicit bridge into Flow line processing.

Accepted source categories remain current behavior:
- `stdin`
- list of strings
- existing Flow

This contract does not redefine line splitting or item representation.

### 3.4 `each`, `collect`, and `run`

`each`, `collect`, and `run` accept only Seq-compatible public values:
- list
- Flow

They must not accept raw `stdin` directly.

Current behavior remains:
- `each(f, list)` returns a lazy tap-style Flow stage that emits the original list items when consumed.
- `each(f, Flow)` returns a lazy tap-style Flow stage that emits original Flow items when consumed.
- `collect(list)` returns the ordered list values.
- `collect(Flow)` materializes emitted Flow items into a list.
- `run(list)` traverses the list and returns `nil`.
- `run(Flow)` consumes the Flow to completion and returns `nil`.

### 3.5 Pipe mode

Pipe mode remains unchanged:
- `genia -p 'stage_expr'` runs `stage_expr` over `stdin |> lines`.
- Pipe mode consumes the final Flow automatically.
- Pipe mode expects the stage expression to produce a Flow.
- Explicit unbound `stdin` remains rejected in pipe mode.
- Explicit unbound `run` remains rejected in pipe mode.

Valid pipe mode:
```bash
printf 'a\nb\n' | genia -p 'each(print)'
```

Invalid pipe mode remains invalid:
```bash
printf 'a\nb\n' | genia -p 'stdin |> lines |> each(print)'
printf 'a\nb\n' | genia -p 'each(print) |> run'
```

---

## 4. SEMANTICS

Evaluation behavior:
- Ordinary pipeline evaluation is unchanged.
- `stdin |> lines` adapts stdin into a lazy Flow.
- `stdin` passed directly to Seq-compatible terminal helpers is an invalid source.
- No implicit Value -> Flow conversion is added.
- No implicit host capability -> Seq conversion is added.

Matching behavior:
- None. This contract does not alter pattern matching or case syntax.

Edge cases:
- Empty stdin adapted through `lines` follows current `lines(stdin)` behavior.
- Reusing a Flow created from `stdin |> lines` follows current single-use Flow behavior.
- `stdin()` compatibility behavior is unchanged by this contract.
- Lists remain eager and reusable.
- Flow remains lazy, pull-based, source-bound, and single-use.

Error behavior:
- Direct raw `stdin` passed to `each`, `collect`, or `run` must fail with a Genia-facing Seq-compatible diagnostic.
- The diagnostic must name the accepted public Seq-compatible values: list or Flow.
- The diagnostic should point users toward `stdin |> lines` when the received value is stdin.
- Diagnostics must not expose Python iterator/generator implementation details.

Preferred diagnostic wording shape:
```text
<helper> expected a Seq-compatible value (list or Flow); received stdin. Use stdin |> lines to adapt stdin into a Flow.
```

Exact stderr/exception wording may be finalized in Test/Implementation if current diagnostics differ, but the user-facing facts above are required.

---

## 5. FAILURE

Failure causes:
- `collect(stdin)` or `stdin |> collect`.
- `run(stdin)` or `stdin |> run`.
- `each(f, stdin)` or `stdin |> each(f)`.
- Any equivalent direct raw stdin use as a Seq-compatible terminal source.

Failure result:
- Runtime error / normalized stderr according to the active execution surface.
- Error must be deterministic enough to test.
- Error must be Genia-facing.

What does not happen:
- No implicit call to `lines(stdin)`.
- No raw stdin direct traversal.
- No Python iterator/generator exposure.
- No new public `Seq` value.
- No change to pipe mode's implicit `stdin |> lines` wrapper.

---

## 6. INVARIANTS

- Seq is semantic terminology, not a public runtime surface.
- The only implemented direct public Seq-compatible values are list and Flow.
- `stdin` is a host-backed input capability, not a Seq-compatible public value.
- `stdin` enters Flow processing through `lines(stdin)`.
- Pipe mode remains sugar around `stdin |> lines` plus automatic final Flow consumption.
- `each`, `collect`, and `run` must not silently adapt raw `stdin`.
- Value/Flow crossings remain explicit.
- Iterator/generator mechanics remain host-internal.
- No Core IR changes are introduced.
- No parser changes are introduced.

---

## 7. EXAMPLES

Minimal valid examples:

```genia
stdin |> lines |> collect
```

```genia
stdin |> lines |> each(print) |> run
```

Minimal invalid examples:

```genia
stdin |> collect
```

```genia
stdin |> each(print) |> run
```

Pipe-mode valid example:

```bash
printf 'a\nb\n' | genia -p 'each(print)'
```

Real command-mode example:

```bash
printf '10\noops\n20\n' | genia -c 'stdin |> lines |> keep_some(parse_int) |> collect |> sum'
```

---

## 8. NON-GOALS

Explicitly not included:
- raw stdin direct Seq compatibility
- public Seq helper/type/syntax
- new Core IR nodes
- parser changes
- async streams
- scheduler semantics
- selective receive
- direct Python generator exposure
- arbitrary host capability Seq adaptation
- broad pipe-mode redesign
- `lines` redesign
- changing list/Flow behavior of `each`, `collect`, or `run`

---

## 9. DOC NOTES

`GENIA_STATE.md` should describe:
- Seq is semantic terminology only.
- Direct Seq-compatible public values are list and Flow.
- `stdin` is not direct Seq-compatible.
- `stdin` enters Flow via `lines(stdin)`.
- Pipe mode injects `stdin |> lines` internally.

Maturity label:
- Partial.

Docs that likely need wording review:
- `GENIA_STATE.md`
- `GENIA_REPL_README.md`
- `README.md`
- `docs/cheatsheet/piepline-flow-vs-value.md`
- `docs/cheatsheet/unix-power-mode.md`
- `docs/cheatsheet/core.md` if it mentions Seq/stdin/Flow terminals
- `spec/flow/README.md`

Documentation rule:
- Do not describe stdin as a direct Seq-compatible public value.
- Say: `stdin` is adapted into Flow by `lines`.
- Say: pipe mode already performs that adaptation.

---

## 10. FINAL CHECK

- Precise and testable: YES.
- No implementation details required for behavior: YES.
- No scope expansion: YES.
- Consistent with `GENIA_STATE.md`: YES.
- Contract decision made: YES — bridge-only stdin boundary.

Next phase:
- Design may proceed.
- Test/Docs/Audit should proceed after Design.
- Implementation should run only if tests expose missing diagnostics or current behavior fails the contract.
