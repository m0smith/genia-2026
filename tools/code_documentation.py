"""Inventory native source contracts and reject new or changed documentation debt.

The checker establishes presence and source association, not semantic quality.
Its legacy baseline is temporary debt and must never grow against the PR base.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import fields, is_dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess


LANGUAGES = {'.py': 'python', '.genia': 'genia', '.cpp': 'cpp', '.hpp': 'cpp',
             '.h': 'cpp', '.ts': 'typescript', '.tsx': 'tsx', '.js': 'typescript',
             '.jsx': 'tsx', '.mjs': 'typescript', '.cjs': 'typescript', '.sh': 'bash',
             '.rs': 'rust', '.go': 'unsupported', '.java': 'unsupported',
             '.ps1': 'unsupported', '.c': 'unsupported', '.toml': 'config', '.wit': 'config',
             '.yml': 'config', '.yaml': 'config', '.cmake': 'config'}


def digest(text):
    """Return the stable SHA-256 fingerprint of an exact source region."""
    return hashlib.sha256(text.encode()).hexdigest()


def record(path, language, binding, kind, source, documented, line=1):
    """Build an identity-bearing inventory record without treating debt as a waiver."""
    return dict(id=f'{path}::{kind}::{binding}', path=path, language=language,
                binding=binding, kind=kind, fingerprint=digest(source),
                documented=bool(documented), line=line)


def comment_before(lines, line):
    """Recognize a nonempty associated comment immediately above a declaration."""
    if line <= 2:
        return False
    previous = lines[line - 2].strip()
    if not previous or not re.match(r'(//|/\*|\*|#\s)', previous):
        return False
    block = previous
    if previous.endswith('*/'):
        index = line - 3
        while '/*' not in block and index >= 0:
            block = lines[index].strip() + '\n' + block
            index -= 1
    return bool(re.search(r'[\w]', re.sub(r'[/#*]', '', block)))


def module_comment(source):
    """Recognize explanatory leading comments, excluding shebangs and preprocessor directives."""
    for line in source.splitlines()[:30]:
        text = line.strip()
        if not text or text.startswith('#!') or text in ('#pragma once',):
            continue
        return bool(re.match(r'(//\s*\S|/\*|#\s+\S)', text))
    return False


def discover(language, source, path):
    """Return documented bindings and explicit gaps, including parser failures.

    Python/Genia use native ASTs; C++, TypeScript and shell use Tree-sitter.
    Named tests may expose their contract in their descriptive name. Production
    internals and test helpers receive no implicit visibility exemption.
    """
    lines = source.splitlines()
    records = []
    if language == 'python':
        try:
            root = ast.parse(source)
        except SyntaxError:
            return [record(path, language, '<parse>', 'parse_error', source, False)]
        purpose = bool(ast.get_docstring(root)) or not root.body
        records.append(record(path, language, '<module>', 'module', source, purpose))

        def visit(node, prefix=''):
            """Walk nested declarations with lexical qualification for baseline identities."""
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    name = prefix + child.name
                    doc = ast.get_docstring(child)
                    test = ('tests/' in path and child.name.startswith('test_')
                            and len(child.name.split('_')) >= 4)
                    region = '\n'.join(lines[child.lineno - 1:child.end_lineno])
                    records.append(record(path, language, name, 'binding', region,
                                          bool(doc and doc.strip()) or test, child.lineno))
                    visit(child, name + '.')
                else:
                    visit(child, prefix)
        visit(root)
    elif language == 'genia':
        from genia.ast_nodes import AnnotatedNode, FuncDef, OpenFuncDef, NamedPatternDef
        from genia.lexer import lex
        from genia.parser import Parser
        from tools.lint_doc import lint_doc
        records.append(record(path, language, '<module>', 'module', source, module_comment(source)))
        try:
            nodes = Parser(lex(source), source=source, filename=path).parse_program()
        except (SyntaxError, ValueError, RecursionError):
            return records + [record(path, language, '<parse>', 'parse_error', source, False)]

        def visit_genia(node, prefix='', documentation=None):
            """Walk native declarations and carry attached documentation to their target."""
            if isinstance(node, AnnotatedNode):
                docs = [a.value.value for a in node.annotations
                        if a.name == 'doc' and isinstance(getattr(a.value, 'value', None), str)]
                visit_genia(node.target, prefix, docs[0] if docs else None)
                return
            if isinstance(node, (FuncDef, OpenFuncDef, NamedPatternDef)):
                name = prefix + node.name
                span = node.span
                region = '\n'.join(lines[span.line - 1:span.end_line]) if span else repr(node)
                doc = documentation or getattr(node, 'docstring', None)
                valid = bool(doc and not any(f.severity.value == 'error' for f in lint_doc(doc)))
                records.append(record(path, language, name, 'binding', region, valid,
                                      span.line if span else 1))
                prefix = name + '.'
            if is_dataclass(node):
                for f in fields(node):
                    if f.name in ('span', 'annotations', 'docstring'):
                        continue
                    value = getattr(node, f.name)
                    if isinstance(value, list):
                        for item in value:
                            visit_genia(item, prefix)
                    elif is_dataclass(value):
                        visit_genia(value, prefix)
        for node in nodes:
            visit_genia(node)
    elif language in ('cpp', 'typescript', 'tsx', 'bash', 'rust'):
        from tree_sitter import Language, Parser
        if language == 'cpp':
            import tree_sitter_cpp as grammar
            capsule = grammar.language()
        elif language == 'rust':
            import tree_sitter_rust as grammar
            capsule = grammar.language()
        elif language == 'bash':
            import tree_sitter_bash as grammar
            capsule = grammar.language()
        else:
            import tree_sitter_typescript as grammar
            capsule = grammar.language_tsx() if language == 'tsx' else grammar.language_typescript()
        encoded = source.encode()
        parser = Parser(Language(capsule))
        tree = parser.parse(encoded)
        root = tree.root_node
        records.append(record(path, language, '<module>', 'module', source, module_comment(source)))
        if root.has_error:
            records.append(record(path, language, '<parse>', 'parse_error', source, False))

        def text(node):
            """Decode one Tree-sitter UTF-8 region without changing its spelling."""
            return encoded[node.start_byte:node.end_byte].decode() if node else ''

        def visit_tree(node, prefix=''):
            """Associate declaration comments, including named callbacks and class methods."""
            kinds = {'function_definition', 'function_declaration', 'method_definition',
                     'class_declaration', 'class_specifier', 'struct_specifier', 'enum_specifier',
                     'function_item', 'struct_item', 'enum_item', 'trait_item'}
            named_arrow = (node.type == 'variable_declarator' and
                           node.child_by_field_name('value') is not None and
                           node.child_by_field_name('value').type in ('arrow_function', 'function_expression'))
            is_declaration = (language == 'cpp' and node.type in ('declaration', 'field_declaration')
                              and any(c.type == 'function_declarator' for c in node.named_children))
            if node.type in kinds or named_arrow or is_declaration:
                name_node = node.child_by_field_name('name')
                if name_node is None:
                    declarator = node.child_by_field_name('declarator')
                    while declarator and declarator.child_by_field_name('declarator'):
                        declarator = declarator.child_by_field_name('declarator')
                    name_node = declarator
                name = text(name_node)
                if name:
                    start = node.start_point.row + 1
                    # Export/lexical wrappers own the adjacent comment in TypeScript.
                    if node.parent and node.parent.type in ('export_statement', 'lexical_declaration'):
                        start = node.parent.start_point.row + 1
                    records.append(record(path, language, prefix + name, 'binding', text(node),
                                          comment_before(lines, start), start))
                    if node.type in ('class_declaration', 'class_specifier', 'struct_specifier',
                                     'function_definition', 'function_declaration'):
                        prefix += name + '.'
            if node.type == 'impl_item':
                prefix += text(node.child_by_field_name('type')) + '::'
            if node.type == 'namespace_definition':
                prefix += text(node.child_by_field_name('name')) + '::'
            for child in node.named_children:
                visit_tree(child, prefix)
        visit_tree(root)
    elif language == 'config':
        records.append(record(path, language, '<module>', 'module', source, module_comment(source)))
    else:
        records.append(record(path, language, '<unsupported>', 'unsupported', source, False))
    # Repeated Genia clauses and overloaded declarations share one documented contract.
    groups = {}
    for r in records:
        if r['id'] in groups:
            old = groups[r['id']]
            old['fingerprint'] = digest(old['fingerprint'] + r['fingerprint'])
            old['documented'] = ((old['documented'] or r['documented']) if language == 'genia'
                                 else (old['documented'] and r['documented']))
        else:
            groups[r['id']] = r
    return list(groups.values())


def assess(records, baseline, exemptions):
    """Reject new/changed gaps, resolved debt and stale or unreasoned exemptions."""
    errors = []
    current = {r['id']: r for r in records}
    for key, waiver in exemptions.items():
        r = current.get(key)
        if not r or not waiver.get('reason', '').strip() or waiver.get('fingerprint') != r['fingerprint']:
            errors.append(f'Invalid or stale exemption: {key}')
    for r in records:
        key = r['id']
        exempt = key in exemptions and exemptions[key].get('reason', '').strip() and exemptions[key].get('fingerprint') == r['fingerprint']
        if not r['documented'] and not exempt and baseline.get(key) != r['fingerprint']:
            errors.append(f'New or changed documentation gap: {key}:{r["line"]}')
    for key, fingerprint in baseline.items():
        r = current.get(key)
        if not r or r['documented'] or key in exemptions:
            errors.append(f'Remove resolved/stale baseline entry: {key}')
    return errors


def baseline_errors(previous, current):
    """Allow debt removal only; reject new identities and changed fingerprints."""
    return [f'Baseline expansion/change: {key}' for key, value in current.items()
            if previous.get(key) != value]


def inventory(root, manifest):
    """Discover tracked maintained files, with reasoned exclusions kept in the report."""
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
    records, excluded = [], []
    for path in filter(None, tracked):
        file = root / path
        if not file.is_file():
            continue
        reason = next((item['reason'] for item in manifest.get('exclude', [])
                       if path == item['path'] or path.startswith(item['path'].rstrip('/') + '/')), None)
        if reason:
            excluded.append(dict(path=path, reason=reason))
            continue
        language = LANGUAGES.get(file.suffix)
        if file.name == 'CMakeLists.txt':
            language = 'config'
        if language == 'config' and not (path.startswith('.github/workflows/') or file.suffix in ('.cmake', '.toml', '.wit') or file.name in ('CMakeLists.txt', 'pyproject.toml')):
            continue  # Declarative specs/data are covered by their existing contract checks.
        if language is None and file.read_bytes().startswith(b'#!'):
            language = 'bash' if b'sh' in file.read_bytes().split(b'\n')[0] else 'unsupported'
        if language:
            records.extend(discover(language, file.read_text(), path))
    return sorted(records, key=lambda r: r['id']), excluded


def parent_baseline(root, base_ref, baseline_file, records):
    """Read debt at the PR base, or validate a first bootstrap against base source.

    Initial rollout has no parent baseline. Only gaps already present with the
    same identity and fingerprint in the target source may enter that baseline.
    """
    result = subprocess.run(['git', 'show', f'{base_ref}:{baseline_file}'],
                            cwd=root, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)['gaps']
    previous = {}
    languages = {r['path']: r['language'] for r in records}
    for path, language in languages.items():
        source = subprocess.run(['git', 'show', f'{base_ref}:{path}'], cwd=root,
                                capture_output=True, text=True)
        if source.returncode == 0:
            for r in discover(language, source.stdout, path):
                if not r['documented']:
                    previous[r['id']] = r['fingerprint']
    return previous


def main(argv=None):
    """Check one checkout or explicitly bootstrap its initial reviewed legacy baseline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--manifest', default='.github/code-documentation.json')
    parser.add_argument('--baseline', default='.github/code-documentation-baseline.json')
    parser.add_argument('--base-ref')
    parser.add_argument('--inventory', type=Path)
    parser.add_argument('--write-baseline', action='store_true')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    manifest = json.loads((root / args.manifest).read_text())
    records, excluded = inventory(root, manifest)
    baseline_path = root / args.baseline
    if args.inventory:
        args.inventory.write_text(json.dumps(dict(schema_version=1, records=records, excluded=excluded), indent=2) + '\n')
    if args.write_baseline:
        if baseline_path.exists():
            parser.error('Bootstrap cannot overwrite an existing baseline; remove resolved entries explicitly.')
        baseline_path.write_text(json.dumps(dict(schema_version=1, gaps={r['id']: r['fingerprint'] for r in records if not r['documented']}), indent=2) + '\n')
    baseline = json.loads(baseline_path.read_text())['gaps']
    errors = assess(records, baseline, manifest.get('exemptions', {}))
    if args.base_ref:
        previous = parent_baseline(root, args.base_ref, args.baseline, records)
        errors.extend(baseline_errors(previous, baseline))
        old_manifest = subprocess.run(['git', 'show', f'{args.base_ref}:{args.manifest}'], cwd=root, capture_output=True, text=True)
        if old_manifest.returncode == 0:
            old = json.loads(old_manifest.stdout)
            for item in manifest.get('exclude', []):
                if item not in old.get('exclude', []):
                    errors.append('New or changed exclusion requires a separate reviewed policy change: ' + item['path'])
            for key, value in manifest.get('exemptions', {}).items():
                if old.get('exemptions', {}).get(key) != value:
                    errors.append('New or changed exemption requires a separate reviewed policy change: ' + key)
    for error in errors:
        print(error)
    print(f'{len(records)} records; {len(baseline)} legacy gaps; {len(excluded)} classified exclusions; {len(errors)} errors')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
