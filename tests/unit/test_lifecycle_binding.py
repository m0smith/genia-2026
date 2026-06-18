import importlib

import pytest


def _binding_module():
    return importlib.import_module("genia.lifecycle_binding")


def _annotation(name, metadata=None, *, line=1):
    lifecycle_binding = _binding_module()
    return lifecycle_binding.AnnotationInfo(
        name=name,
        metadata={} if metadata is None else metadata,
        source_location={"file": "suite.genia", "line": line, "source": f"@{name}"},
    )


def _candidate(
    name,
    value,
    annotations,
    *,
    source_identity="suite.genia",
    source_index=1,
):
    lifecycle_binding = _binding_module()
    return lifecycle_binding.AnnotationCandidate(
        name=name,
        value=value,
        annotations=annotations,
        source_location={"file": source_identity, "line": source_index},
        source_identity=source_identity,
        source_index=source_index,
    )


def _binding(
    *,
    annotation_name="setup",
    filters=None,
    ordering="source_order",
    required=False,
    participant_kind="callable",
):
    lifecycle_binding = _binding_module()
    return lifecycle_binding.LifecycleAnnotationBinding(
        phase="test_before",
        annotation_name=annotation_name,
        filters={} if filters is None else filters,
        ordering=ordering,
        required=required,
        participant_kind=participant_kind,
        failure_policy="diagnostic",
    )


def _discover(binding, candidates):
    return _binding_module().discover_lifecycle_participants(binding, candidates)


def _participant_names(result):
    return [participant.declaration_name for participant in result.participants]


def _diagnostic_reasons(result):
    return [diagnostic.reason for diagnostic in result.diagnostics]


def test_optional_binding_with_zero_candidates_succeeds_without_diagnostics():
    result = _discover(_binding(required=False), [])

    assert result.phase == "test_before"
    assert result.participants == []
    assert result.diagnostics == []


def test_required_binding_with_zero_candidates_reports_deterministic_diagnostic():
    result = _discover(_binding(required=True), [])

    assert result.participants == []
    assert _diagnostic_reasons(result) == [
        "required lifecycle annotation binding found no candidates for @setup"
    ]


def test_annotation_name_matching_selects_only_matching_annotations():
    selected = _candidate("selected", lambda: None, [_annotation("setup")], source_index=1)
    ignored = _candidate("ignored", lambda: None, [_annotation("test")], source_index=2)

    result = _discover(_binding(annotation_name="setup"), [ignored, selected])

    assert _participant_names(result) == ["selected"]
    assert result.diagnostics == []


def test_exact_metadata_filters_include_matching_metadata():
    candidate = _candidate(
        "setup_test",
        lambda: None,
        [_annotation("setup", {"scope": "test", "role": "db"})],
    )

    result = _discover(_binding(filters={"scope": "test"}), [candidate])

    assert _participant_names(result) == ["setup_test"]
    assert result.diagnostics == []


def test_exact_metadata_filters_exclude_non_matching_metadata():
    candidate = _candidate(
        "setup_module",
        lambda: None,
        [_annotation("setup", {"scope": "module"})],
    )

    result = _discover(_binding(filters={"scope": "test"}), [candidate])

    assert result.participants == []
    assert result.diagnostics == []


def test_callable_participant_kind_accepts_callable_values():
    def setup():
        raise AssertionError("binding discovery must not execute participants")

    result = _discover(_binding(participant_kind="callable"), [_candidate("setup", setup, [_annotation("setup")])])

    assert _participant_names(result) == ["setup"]
    assert result.participants[0].value is setup
    assert result.diagnostics == []


def test_callable_participant_kind_rejects_non_callable_values_with_diagnostic():
    result = _discover(_binding(participant_kind="callable"), [_candidate("not_callable", 1, [_annotation("setup")])])

    assert result.participants == []
    assert _diagnostic_reasons(result) == [
        "lifecycle participant not_callable for @setup expected callable, got int"
    ]


def test_source_order_ordering_is_deterministic():
    candidates = [
        _candidate("third", lambda: None, [_annotation("setup")], source_index=3),
        _candidate("first", lambda: None, [_annotation("setup")], source_index=1),
        _candidate("second", lambda: None, [_annotation("setup")], source_index=2),
    ]

    result = _discover(_binding(ordering="source_order"), candidates)

    assert _participant_names(result) == ["first", "second", "third"]


def test_reverse_source_order_ordering_is_deterministic():
    candidates = [
        _candidate("first", lambda: None, [_annotation("setup")], source_index=1),
        _candidate("third", lambda: None, [_annotation("setup")], source_index=3),
        _candidate("second", lambda: None, [_annotation("setup")], source_index=2),
    ]

    result = _discover(_binding(ordering="reverse_source_order"), candidates)

    assert _participant_names(result) == ["third", "second", "first"]


def test_stable_name_order_ordering_is_deterministic():
    candidates = [
        _candidate("bravo", lambda: None, [_annotation("setup")], source_index=1),
        _candidate("alpha", lambda: None, [_annotation("setup")], source_index=2),
        _candidate("charlie", lambda: None, [_annotation("setup")], source_index=3),
    ]

    result = _discover(_binding(ordering="stable_name_order"), candidates)

    assert _participant_names(result) == ["alpha", "bravo", "charlie"]


def test_duplicate_participant_selection_reports_diagnostic_and_keeps_at_most_one_participant():
    candidate = _candidate(
        "setup_once",
        lambda: None,
        [
            _annotation("setup", {"scope": "test"}, line=1),
            _annotation("setup", {"scope": "test"}, line=2),
        ],
    )

    result = _discover(_binding(filters={"scope": "test"}), [candidate])

    assert _participant_names(result) == ["setup_once"]
    assert _diagnostic_reasons(result) == [
        "duplicate lifecycle participant selected for @setup: setup_once"
    ]


def test_unsupported_ordering_reports_deterministic_error():
    with pytest.raises(
        ValueError,
        match="invalid lifecycle annotation binding at binding.ordering: unsupported ordering random_order",
    ):
        _discover(_binding(ordering="random_order"), [])
