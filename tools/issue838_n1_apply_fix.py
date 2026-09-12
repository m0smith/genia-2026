from pathlib import Path

p = Path("tools/issue838_n1_apply.py")
text = p.read_text()
old = '''replace(
    "src/genia/lowering.py",
    "return IrLiteral(node.value, span=node.span)",
    "return IrLiteral(node.value.portable_payload(), span=node.span)",
    1,
)
'''
new = '''replace(
    "src/genia/lowering.py",
    "    if isinstance(node, Number):\\n        return IrLiteral(node.value, span=node.span)\\n",
    "    if isinstance(node, Number):\\n        return IrLiteral(node.value.portable_payload(), span=node.span)\\n",
    1,
)
'''
if text.count(old) != 1:
    raise SystemExit(f"expected one broad Number lowering patch, found {text.count(old)}")
p.write_text(text.replace(old, new))
