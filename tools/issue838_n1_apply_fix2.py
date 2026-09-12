from pathlib import Path

p = Path("tools/issue838_n1_apply.py")
text = p.read_text()
old = '''replace(
    "src/genia/lowering.py",
    "return IrPatLiteral(pattern.value)",
    "return IrPatLiteral(pattern.value.portable_payload())",
    1,
)
'''
new = '''replace(
    "src/genia/lowering.py",
    "    if isinstance(pattern, Number):\\n        return IrPatLiteral(pattern.value)\\n",
    "    if isinstance(pattern, Number):\\n        return IrPatLiteral(pattern.value.portable_payload())\\n",
    1,
)
'''
if text.count(old) != 1:
    raise SystemExit(f"expected one broad Number pattern patch, found {text.count(old)}")
p.write_text(text.replace(old, new))
