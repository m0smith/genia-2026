# #1261 Slice B review-fix RED evidence (Codex FAIL at 888f2123, findings M1/M2/M5)

Starting head `888f2123d5d0182cda3d7ddcccafd76b0d87b308`. No production file is changed in this RED commit.

- `tests/unit/test_model_b_slice_b_races.py::test_m1_function_writer_cannot_extend_group_after_name_becomes_immutable`: **fails** `({'result': <function x/2>}, {'result': None})`: the function writer and the immutable commit both succeed (Codex's M1 interleaving: writer paused after its immutability check, `x` committed immutable over group `g`, writer resumes and adds a clause).
- `...::test_m2_metadata_writer_cannot_land_in_the_partial_publication_window`: **fails** (`meta_outcome == {'result': None}`): an unauthorized `merge_binding_metadata` succeeds while the commit is paused between `values[x]` and policy publication.
- `...::test_m2_declaration_owned_metadata_still_attaches_after_commit`: passes; guards the authorized attachment path that the fix must preserve.
- `spec/eval/model-b-b-cell-mutation-observable.yaml` (M5): `c =: cell(1); cell_send(c, (s) -> s + 1); _r25_await_idle(); cell_get(c)` expects `2`; requires `immutable_bindings` and `cell_primitives`; added to the C++ gap's affected tests. It passes on Python already (coverage addition, not a defect); shared subset `selected=27 passed=27`.
- Determinism: pauses use a patched hook (`Env._reject_immutable_write`) and a pausing `assignable` set. Every wait is bounded, and a correct implementation, where the paused writer holds the lock and the competitor blocks, still terminates.
