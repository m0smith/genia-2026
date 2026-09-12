# Issue #836 — Portable Cross-Module Shared-Spec Pre-flight

Status: **Pre-flight complete.** This is conformance infrastructure analysis,
not language authority; `GENIA_STATE.md` remains final authority.

## Inventory and gap

At starting revision `125bd4a2da35f25207cbcf8730d3e72e5d742ef5`, eval/error
cases normalize one `input.source` string. The in-process Python adapter passes
that string to command-mode execution; the R16 external-host request carries
the same string. Capability selection already treats `requires:
[open_functions]` as applicable only for a host declaring the capability
`supported`.

R20 has shared single-file parse, Core IR, eval, and error evidence. Its
cross-module interface/contribution/linking obligations are instead exercised
only by `tests/unit/test_r20_open_functions_cross_module.py`, which creates real
Python-host filesystem fixtures. The portable gap is therefore fixture input
and transport, not parser, evaluator, module, or open-function semantics.

The minimum extension is an optional, normalized logical module fixture on the
existing eval/error input. It must carry deterministic relative `.genia` paths,
contents, and one entry path through the existing R16 eval request. Materializing
that model is a private host-adapter choice.

## Portability analysis

1. **Semantic owner:** existing R20 module/open-function contracts; #836 owns
   only shared-spec fixture and adapter evidence.
2. **Core IR impact:** none.
3. **Host boundary:** every host receives the same logical files and entry path;
   hosts may realize them differently.
4. **Determinism:** paths, contents, entry selection, validation, request JSON,
   outcomes, and diagnostics are deterministic.
5. **Unsupported behavior:** an unmet `open_functions` requirement is reported
   `unsupported` before case execution and is never a pass.
6. **Failure normalization:** malformed fixtures fail spec loading; evaluated
   language failures retain existing portable stderr/exit-code comparison.
7. **Non-portable assumptions excluded:** absolute paths, `..`, temporary
   directory names, Python loader objects, raw Python exceptions, and filesystem
   layout are not fixture semantics.

## Scope decision

Proceed with fixture contract/design and failing tests. Do not modify language
semantics, syntax, Core IR, module exports, or `GENIA_STATE.md`.
