"""Development-tool coverage rules; these do not establish Genia portability."""

import pytest

from tools.code_documentation import discover, assess, baseline_errors


@pytest.mark.parametrize("language,source", [
    ("python", '"""Module purpose."""\ndef f(x):\n    return x\n'),
    ("genia", '# Module purpose.\nf(x) = x\n'),
    ("cpp", '// Module purpose.\nint f(int x) { return x; }\n'),
    ("typescript", '// Module purpose.\nexport function f(x: number) { return x; }\n'),
    ("bash", '# Module purpose.\nf() { echo hello; }\n'),
])
def test_named_function_requires_native_documentation(language, source):
    records = discover(language, source, "sample")
    assert any(r["binding"].endswith("f") and not r["documented"] for r in records)


@pytest.mark.parametrize("language,source", [
    ("python", '"""Module purpose."""\ndef f(x):\n    """Return x unchanged."""\n    return x\n'),
    ("genia", '# Module purpose.\n@doc "Return x unchanged."\nf(x) = x\n'),
    ("cpp", '// Module purpose.\n\n/// Return x unchanged.\nint f(int x) { return x; }\n'),
    ("typescript", '// Module purpose.\n\n/** Return x unchanged. */\nexport function f(x: number) { return x; }\n'),
    ("bash", '# Module purpose.\n\n# Write hello to stdout.\nf() { echo hello; }\n'),
])
def test_native_documentation_is_associated_with_binding(language, source):
    assert all(r["documented"] for r in discover(language, source, "sample"))


def test_internal_nested_helper_is_not_exempt():
    source = '"""Purpose."""\ndef outer():\n    """Build a helper."""\n    def _impl():\n        return 1\n    return _impl\n'
    records = discover("python", source, "sample.py")
    assert any(r["binding"] == "outer._impl" and not r["documented"] for r in records)


def test_clear_test_name_satisfies_test_contract_but_helper_does_not():
    records = discover("python", '"""Purpose."""\ndef test_invalid_input_is_rejected():\n    assert True\ndef helper():\n    return 1\n', "tests/test_example.py")
    assert next(r for r in records if r["binding"].startswith("test_"))["documented"]
    assert not next(r for r in records if r["binding"] == "helper")["documented"]


def test_parse_failure_is_an_explicit_gap():
    records = discover("python", "def broken(:", "sample.py")
    assert any(r["kind"] == "parse_error" for r in records)


def test_genia_multiclause_and_multiline_doc():
    source = '# Purpose.\n@doc """Return the greatest common divisor.\n\n## Returns\nAn integer.\n"""\nopen gcd(a, 0) = a\ngcd(a, b) = gcd(b, a % b)\n'
    records = discover("genia", source, "sample.genia")
    assert any(r["binding"] == "gcd" and r["documented"] for r in records)
    assert not any(r["kind"] == "parse_error" for r in records)


def test_named_typescript_arrow_and_cpp_method_are_discovered():
    ts = discover("typescript", '// Purpose.\nconst work = (x:number) => x;\n', "sample.ts")
    cpp = discover("cpp", '// Purpose.\nclass C { public: int f() { return 1; } };', "sample.hpp")
    assert any(r["binding"].endswith("work") for r in ts)
    assert any(r["binding"].endswith("f") for r in cpp)


def test_baseline_cannot_exchange_one_gap_for_another_or_accept_edits():
    first = discover("python", '"""Purpose."""\ndef f():\n    return 1\n', "sample.py")
    baseline = {r["id"]: r["fingerprint"] for r in first if not r["documented"]}
    changed = discover("python", '"""Purpose."""\ndef f():\n    return 2\n', "sample.py")
    assert assess(first, baseline, {}) == []
    assert assess(changed, baseline, {})
    renamed = discover("python", '"""Purpose."""\ndef g():\n    return 1\n', "sample.py")
    assert assess(renamed, baseline, {})
    moved = discover("python", '"""Purpose."""\ndef f():\n    return 1\n', "moved.py")
    assert assess(moved, baseline, {})


def test_resolved_baseline_entry_is_stale():
    records = discover("python", '"""Purpose."""\ndef f():\n    """Return one."""\n    return 1\n', "sample.py")
    binding = next(r for r in records if r["binding"] == "f")
    assert assess(records, {binding["id"]: binding["fingerprint"]}, {})


def test_exemption_requires_reason_exact_fingerprint_and_current_binding():
    records = discover("python", '"""Purpose."""\ndef f():\n    return 1\n', "sample.py")
    r = next(r for r in records if r["binding"] == "f")
    valid = {r["id"]: {"reason": "Trivial pure constant helper.", "fingerprint": r["fingerprint"]}}
    assert assess(records, {}, valid) == []
    assert assess(records, {}, {r["id"]: {"reason": "", "fingerprint": r["fingerprint"]}})
    assert assess(records, {}, {"missing": {"reason": "Old helper.", "fingerprint": "x"}})


def test_target_branch_baseline_only_allows_removal():
    assert baseline_errors({"a": "old"}, {}) == []
    assert baseline_errors({}, {"new": "hash"})
    assert baseline_errors({"a": "old"}, {"a": "changed"})


def test_cpp_namespaces_have_distinct_debt_identities():
    records = discover('cpp', '// Purpose.\nnamespace a { int f() {return 1;} }\nnamespace b { int f() {return 2;} }', 'sample.hpp')
    names = {r['binding'] for r in records}
    assert 'a::f' in names and 'b::f' in names


def test_documented_overload_does_not_hide_an_undocumented_overload():
    records = discover('cpp', '// Purpose.\n\n/// Return the integer.\nint f(int x) {return x;}\ndouble f(double x) {return x;}', 'sample.hpp')
    assert not next(r for r in records if r['binding'] == 'f')['documented']


def test_large_cpp_tree_keeps_valid_source_positions():
    source = '// Purpose.\nclass C {\n' + '\n'.join(f'int f{i}() {{ return {i}; }}' for i in range(150)) + '\n};'
    records = discover('cpp', source, 'sample.hpp')
    assert len([r for r in records if r['kind'] == 'binding']) == 151
    assert all(1 <= r['line'] <= len(source.splitlines()) for r in records)


def test_initial_baseline_cannot_hide_a_new_binding(tmp_path):
    import subprocess
    from tools.code_documentation import parent_baseline
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=tmp_path, check=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.invalid'], cwd=tmp_path, check=True)
    old = '"""Purpose."""\ndef old():\n    return 1\n'
    (tmp_path / 'sample.py').write_text(old)
    subprocess.run(['git', 'add', '.'], cwd=tmp_path, check=True)
    subprocess.run(['git', 'commit', '-qm', 'Base'], cwd=tmp_path, check=True)
    records = discover('python', old + '\ndef new():\n    return 2\n', 'sample.py')
    previous = parent_baseline(tmp_path, 'HEAD', 'absent.json', records)
    current = {r['id']: r['fingerprint'] for r in records if not r['documented']}
    assert baseline_errors(previous, current) == ['Baseline expansion/change: sample.py::binding::new']


def test_documentation_policy_and_checker_guide_are_published():
    from tools.stage_docs_for_mkdocs import STRATEGY_DOCS, README_LINK_REWRITES
    assert 'docs/contract/code-documentation.md' in STRATEGY_DOCS
    assert 'docs/process/code-documentation.md' in STRATEGY_DOCS
    assert README_LINK_REWRITES['(docs/contract/'] == '(contract/'
    assert README_LINK_REWRITES['(docs/process/'] == '(process/'
