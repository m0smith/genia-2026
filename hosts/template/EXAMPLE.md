# Example: Bringing Up a New Host from the Template

This walkthrough shows how to go from zero to a host that passes at least one shared spec case. Follow each step in order. Do not skip ahead.

---

## Step 1 — Copy the template

Copy this directory to your target host directory:

```bash
cp -r hosts/template/ hosts/<new-host>/
```

Replace `<new-host>` with the host language name (e.g. `go`, `node`, `java`).

---

## Step 2 — Update status and goal

Open `hosts/<new-host>/AGENTS.md` and `hosts/<new-host>/README.md`.

- Change the `# <Host Name> Host` heading to the real host name.
- The `## Status` section must remain `scaffolded, not implemented` until you have working code, tests, and spec coverage.
- Fill in the `## Goal` section with a short description of what this host will provide.

Do **not** change the `## Status` value to `Implemented` until Step 6 confirms coverage.

---

## Step 3 — Choose a target spec category

Pick one spec category to implement first. The recommended starting point is **`eval`** because:

- It requires only source-string execution and stdout/stderr/exit_code capture.
- The eval shared spec cases are the largest and most representative set.
- It proves the core parser + evaluator + output capture pipeline.

The other categories (`ir`, `cli`, `flow`, `error`, `parse`) can follow once `eval` is working.

---

## Step 4 — Implement run_case for one category

Open `hosts/<new-host>/adapter_stub.md` and read the `run_case` contract.

Your host adapter must expose:

```
run_case(spec: LoadedSpec) -> ActualResult
```

For the `eval` category, the minimal implementation is:

1. Read `spec.source` — the Genia source string to evaluate.
2. Run it through your host evaluator.
3. Capture `stdout`, `stderr`, and `exit_code`.
4. Return an `ActualResult` with those three fields.

See `hosts/python/adapter.py` and `hosts/python/exec_eval.py` for the reference implementation.
The authoritative contract is in `docs/host-interop/HOST_INTEROP.md` §Host Adapter and Spec Runner Model.

---

## Step 5 — Run the shared spec runner

```bash
python -m tools.spec_runner
```

The runner will execute all active shared spec cases against your `run_case` implementation.

**Interpreting output:**

- A passing case prints nothing (or a timing line with `--verbose`).
- A failing case prints the case name, expected output, and actual output.
- The runner exits with code 0 when all cases pass, non-zero otherwise.

Start by targeting one `eval` case. Once that passes, work through the rest of the `eval` set before moving to `ir`, `cli`, `flow`, `error`, and `parse`.

---

## Step 6 — Update CAPABILITY_STATUS.md

Open `hosts/<new-host>/CAPABILITY_STATUS.md`.

For each capability you have implemented and verified with passing tests **and** passing shared spec coverage, change its `Status` from `Not Implemented` to `Implemented`.

Rules:
- Do not mark `Implemented` until code, tests, **and** spec coverage all exist.
- Use only capability names from `docs/host-interop/capabilities.md`.
- Add notes in the `Notes` column describing any host-specific limitations.

---

## Step 7 — Update HOST_CAPABILITY_MATRIX.md

Open `docs/host-interop/HOST_CAPABILITY_MATRIX.md`.

Find the row for your host language (or add one if it does not exist yet).

Update **only** the cells for your host. Do not change cells for other hosts.

Rules:
- Status values: `Implemented`, `Not Implemented`, `Python-host-only` (only applies to the Python reference host), `Scaffolded`, `Planned`.
- Do not add a row for `hosts/template/` — the template is not a host.

---

Note: Do not update `GENIA_STATE.md` or shared docs (`GENIA_RULES.md`, `GENIA_REPL_README.md`, `README.md`) unless the new host changes shared observable behavior. Host-local bring-up is not a shared behavior change.

When in doubt, re-read `docs/host-interop/HOST_PORTING_GUIDE.md` and `docs/host-interop/HOST_CAPABILITY_MATRIX.md`.
