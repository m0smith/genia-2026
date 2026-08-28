from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples/r12_cross_mode_grounded_proving.genia"
SHARED_CASES = (
    ROOT / "spec/eval/r12-grounded-cross-mode.yaml",
    ROOT / "spec/flow/r12-grounded-bounded-flow.yaml",
    ROOT / "spec/error/error-r12-grounded-provider-failure.yaml",
    ROOT / "spec/cli/r12-grounded-proving-case.yaml",
    ROOT / "spec/parse/parse-r12-grounded-existing-forms.yaml",
    ROOT / "spec/ir/r12-grounded-existing-ir.yaml",
)


def test_e12_7_proving_example_and_shared_inventory_exist():
    assert EXAMPLE.is_file()
    assert all(path.is_file() for path in SHARED_CASES)


def test_e12_7_example_keeps_every_provider_stage_explicit():
    source = EXAMPLE.read_text(encoding="utf-8")
    for required in (
        "chunk(",
        "apply_raw(embed_call",
        "apply_raw(index_call",
        "apply_raw(retrieve_call",
        "apply_raw(rerank_call",
        "grounding.assemble_grounded_context",
        "grounding.generate_grounded_answer",
        "validate_record",
        "collect_validated",
    ):
        assert required in source
    for forbidden in (
        "retry(",
        "sleep(",
        "grounded_pipeline(",
        "hidden_embed",
    ):
        assert forbidden not in source


def test_e12_7_shared_cases_use_only_explicit_fixture_authority():
    for path in SHARED_CASES[:4]:
        source = path.read_text(encoding="utf-8")
        assert "fixtures: [r12_grounded]" in source
        assert "_retry" not in source
        assert "sleep(" not in source
