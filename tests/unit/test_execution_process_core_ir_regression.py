"""FAILING-TEST PHASE — Group L: Core IR regression.

Design conclusion (`docs/design/execution-process-design.md` §18): NO new
Core IR is required for `execution.process(...)` syntax -- it is an
ordinary dotted-member call, exactly like any other `module.function(...)`
invocation the grammar already supports.

Unlike every other file in this failing-test phase, the structural claim
here is checkable TODAY without any production `execution.process`
implementation: parsing and lowering `execution.process(capability,
request)`-shaped source does not require evaluating it (evaluating it does
require the not-yet-existing builtin, which is a separate concern covered
by `test_execution_process_genia_surface_absent.py`). This test is
therefore expected to PASS now -- it is supporting evidence for the design
conclusion, not a RED test. Per the task instructions: "If the currently
nonexistent builtin prevents full eval lowering from being exercised
naturally, choose the smallest appropriate structural regression test
without weakening the conclusion."

If this test ever fails because lowering introduces a new IR node family
for a call shaped like `x.y(...)`, that is a genuine design blocker
(`docs/design/execution-process-design.md` §18 says to STOP and report a
design blocker rather than modify the architecture) -- do not "fix" this
test by expanding the allowed node-family set.
"""

from __future__ import annotations

import json

from genia.interpreter import Parser, lex, lower_program


# The exact minimal-portable node-family vocabulary from
# spec/manifest.json's core_ir_contract.minimal_portable_node_families,
# duplicated here (not imported) so a manifest edit doesn't silently widen
# what this regression accepts.
_MINIMAL_PORTABLE_NODE_FAMILIES = {
    "IrAnnotation",
    "IrLiteral",
    "IrOptionNone",
    "IrOptionSome",
    "IrVar",
    "IrQuote",
    "IrDelay",
    "IrQuasiQuote",
    "IrUnquote",
    "IrUnquoteSplicing",
    "IrUnary",
    "IrBinary",
    "IrPipeline",
    "IrCall",
    "IrExprStmt",
    "IrBlock",
    "IrList",
    "IrMap",
    "IrSpread",
    "IrCaseClause",
    "IrCase",
    "IrLambda",
    "IrAssign",
    "IrFuncDef",
    "IrNamedPatternDef",
    "IrImport",
    "IrOpenFuncDef",
    "IrOpenContribution",
    "IrOpenUse",
}

_FORBIDDEN_SPECULATIVE_NODE_NAMES = {
    "IrProcess",
    "IrSpawnExternal",
    "IrHostCall",
    "IrShell",
    "IrShellStage",
}


def _lowered_node_type_names(source: str) -> set[str]:
    ast_nodes = Parser(lex(source)).parse_program()
    ir_nodes = lower_program(ast_nodes)

    seen: set[str] = set()

    def walk(obj) -> None:
        if hasattr(obj, "__dataclass_fields__"):
            seen.add(type(obj).__name__)
            for field_name in obj.__dataclass_fields__:
                walk(getattr(obj, field_name))
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                walk(item)
        elif isinstance(obj, dict):
            for item in obj.values():
                walk(item)

    walk(ir_nodes)
    return seen


def test_execution_process_call_lowers_using_only_minimal_portable_node_families():
    source = (
        'execution.process(capability, {executable: quote(host), '
        'args: ["a", "b"], timeout_ms: 1000})'
    )

    node_types = _lowered_node_type_names(source)

    # SourceSpan/Var are non-IR support dataclasses that legitimately appear
    # in the walk; filter to only names that look like IR node families.
    ir_node_types = {name for name in node_types if name.startswith("Ir")}

    assert ir_node_types, "expected at least one IR node from lowering"
    assert ir_node_types <= _MINIMAL_PORTABLE_NODE_FAMILIES, (
        f"execution.process(...) lowered to node families outside the "
        f"approved minimal portable set: {ir_node_types - _MINIMAL_PORTABLE_NODE_FAMILIES}"
    )
    assert not (ir_node_types & _FORBIDDEN_SPECULATIVE_NODE_NAMES), (
        "execution.process(...) must not introduce a speculative process-"
        "specific IR node (contract §15 names IrProcess/IrSpawnExternal/"
        "IrHostCall/a shell AST as explicitly not added)"
    )


def test_execution_process_call_uses_ordinary_call_and_var_nodes_like_any_other_dotted_call():
    """A minimal comparison case: `execution.process(...)` must lower to the
    exact same node-family shape as an arbitrary unrelated dotted call
    `foo.bar(...)` -- proving there is nothing special-cased about this
    particular name at the lowering layer.
    """
    execution_process_types = _lowered_node_type_names(
        "execution.process(capability, {executable: quote(host), args: [], timeout_ms: 1})"
    )
    arbitrary_dotted_call_types = _lowered_node_type_names(
        "some_module.some_function(a, {x: quote(host), y: 2}, [1, 2, 3])"
    )

    execution_process_ir_types = {t for t in execution_process_types if t.startswith("Ir")}
    arbitrary_ir_types = {t for t in arbitrary_dotted_call_types if t.startswith("Ir")}

    assert execution_process_ir_types == arbitrary_ir_types


def test_manifest_core_ir_contract_still_matches_the_frozen_set():
    """Sanity-check this file's duplicated node-family list against
    `spec/manifest.json` -- if these ever disagree, the manifest changed
    without this regression being updated, which would silently widen or
    narrow what this test actually protects.
    """
    with open("spec/manifest.json", encoding="utf-8") as handle:
        manifest = json.load(handle)

    manifest_families = set(
        manifest["core_ir_contract"]["minimal_portable_node_families"]
    )
    assert manifest_families == _MINIMAL_PORTABLE_NODE_FAMILIES
