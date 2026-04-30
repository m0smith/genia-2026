"""
Normalization helpers for the Genia Python host adapter.
"""


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def strip_trailing_newlines(text: str) -> str:
    return text.rstrip("\n")
