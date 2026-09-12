from pathlib import Path

p = Path("tools/issue838_n1_apply.py")
text = p.read_text()
old = '''old = "if isinstance(pattern, IrPatLiteral):\\n        return {} if genia_equal(pattern.value, arg) else None"\nif old not in text:\n    raise SystemExit("pattern_match literal branch not found")\ntext = text.replace(\n    old,\n    "if isinstance(pattern, IrPatLiteral):\\n        expected = materialize_legacy_numeric(pattern.value)\\n        return {} if genia_equal(expected, arg) else None",\n)\n'''
new = '''old = "        return {} if genia_equal(pattern.value, arg) else None"\nif text.count(old) != 1:\n    raise SystemExit(f"pattern_match literal comparison count was {text.count(old)}, expected 1")\ntext = text.replace(\n    old,\n    "        expected = materialize_legacy_numeric(pattern.value)\\n        return {} if genia_equal(expected, arg) else None",\n)\n'''
if text.count(old) != 1:
    raise SystemExit(f"expected one pattern matcher patch block, found {text.count(old)}")
p.write_text(text.replace(old, new))
