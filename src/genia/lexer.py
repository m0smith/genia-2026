import re
from dataclasses import dataclass

# Single source of truth for symbol/operator policy:
# - These characters are always token delimiters/operators in Genia.
# - Clojure-style symbol punctuation that we allow in names is listed below.
# - `name?` and `name!` are ordinary identifiers (no special lexer semantics).
# - `/` is reserved for division and is not allowed inside identifier names.
ALWAYS_OPERATOR_DELIMITERS = frozenset({"+", "*", "/", "%", "=", "<", ">", "|", ",", ";", ":", "@", "(", ")", "{", "}", "[", "]"})
ALLOWED_SYMBOL_PUNCTUATION = frozenset({"_", "?", "!", ".", "$", "-"})
IDENT_START_RE = re.compile(r"[A-Za-z_$]")
IDENT_BODY_RE = re.compile(r"[A-Za-z0-9]")

TOKEN_SPEC = [
    ("NUMBER", r"\d+(?:\.\d+)?"),
    ("STRING", r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\''),
    ("ARROW", r"->"),
    ("EQEQ", r"=="),
    ("NE", r"!="),
    ("LE", r"<="),
    ("GE", r">="),
    ("AND", r"&&"),
    ("OR", r"\|\|"),
    ("PIPE_FWD", r"\|>"),
    ("ASSIGN", r"="),
    ("LT", r"<"),
    ("GT", r">"),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("STAR", r"\*"),
    ("SLASH", r"/"),
    ("PERCENT", r"%"),
    ("BANG", r"!"),
    ("QMARK", r"\?"),
    ("PIPE", r"\|"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("LBRACK", r"\["),
    ("RBRACK", r"\]"),
    ("DOTDOT", r"\.\."),
    ("COMMA", r","),
    ("COLON", r":"),
    ("SEMI", r";"),
    ("AT", r"@"),
    ("COMMENT", r"#[^\n]*"),
    ("NEWLINE", r"\n"),
    ("SKIP", r"[ \t\r]+"),
]
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
STRING_RE = re.compile(r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\'')
PUNCTUATION_TOKENS = [
    ("ARROW", "->"),
    ("EQEQ", "=="),
    ("NE", "!="),
    ("LE", "<="),
    ("GE", ">="),
    ("AND", "&&"),
    ("OR", "||"),
    ("PIPE_FWD", "|>"),
    ("DOTDOT", ".."),
    ("ASSIGN", "="),
    ("LT", "<"),
    ("GT", ">"),
    ("PLUS", "+"),
    ("MINUS", "-"),
    ("STAR", "*"),
    ("SLASH", "/"),
    ("PERCENT", "%"),
    ("BANG", "!"),
    ("QMARK", "?"),
    ("PIPE", "|"),
    ("LPAREN", "("),
    ("RPAREN", ")"),
    ("LBRACE", "{"),
    ("RBRACE", "}"),
    ("LBRACK", "["),
    ("RBRACK", "]"),
    ("COMMA", ","),
    ("COLON", ":"),
    ("SEMI", ";"),
    ("AT", "@"),
]
def _is_identifier_start(ch: str) -> bool:
    if ch == "$":
        return True
    return bool(IDENT_START_RE.fullmatch(ch))


def _is_identifier_part(ch: str) -> bool:
    if IDENT_BODY_RE.fullmatch(ch):
        return True
    if ch in ALWAYS_OPERATOR_DELIMITERS:
        return False
    return ch in ALLOWED_SYMBOL_PUNCTUATION


@dataclass
class Token:
    kind: str
    text: str
    pos: int


@dataclass(frozen=True)
class SourceSpan:
    filename: str
    line: int
    column: int
    end_line: int
    end_column: int


def lex(source: str) -> list[Token]:
    tokens: list[Token] = []
    pos = 0
    length = len(source)

    while pos < length:
        ch = source[pos]

        if ch in " \t\r":
            pos += 1
            continue
        if ch == "\n":
            tokens.append(Token("NEWLINE", ch, pos))
            pos += 1
            continue
        if ch == "#":
            while pos < length and source[pos] != "\n":
                pos += 1
            continue

        number_match = NUMBER_RE.match(source, pos)
        if number_match is not None:
            text = number_match.group()
            tokens.append(Token("NUMBER", text, pos))
            pos += len(text)
            continue

        if source.startswith('glob"', pos):
            literal_start = pos + 4
            i = literal_start + 1
            while i < length:
                if source[i] == "\\":
                    i += 2
                    continue
                if source[i] == '"':
                    text = source[pos:i + 1]
                    tokens.append(Token("GLOB", text, pos))
                    pos = i + 1
                    break
                i += 1
            else:
                raise SyntaxError(f"Unterminated glob pattern literal at {pos}")
            continue

        if ch in "\"'":
            if source.startswith(ch * 3, pos):
                delim = ch * 3
                i = pos + 3
                while i < length:
                    if source.startswith(delim, i):
                        text = source[pos:i + 3]
                        tokens.append(Token("STRING", text, pos))
                        pos = i + 3
                        break
                    if source[i] == "\\":
                        i += 2
                        continue
                    i += 1
                else:
                    raise SyntaxError(f"Unterminated triple-quoted string at {pos}")
            else:
                string_match = STRING_RE.match(source, pos)
                if string_match is None:
                    raise SyntaxError(f"Unexpected character {ch!r} at {pos}")
                text = string_match.group()
                tokens.append(Token("STRING", text, pos))
                pos += len(text)
            continue

        if ch == "$" and pos + 1 < length and source[pos + 1] == "(":
            cmd_start = pos + 2
            depth = 1
            i = cmd_start
            while i < length and depth > 0:
                c = source[i]
                if c == "$" and i + 1 < length and source[i + 1] == "(":
                    raise SyntaxError(f"nested shell stages are not supported at {i}")
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                if depth > 0:
                    i += 1
            if depth != 0:
                raise SyntaxError(f"Unterminated shell stage $(...) at {pos}")
            command = source[cmd_start:i].strip()
            if not command:
                raise SyntaxError(f"shell stage: empty command at {pos}")
            tokens.append(Token("SHELL_STAGE", command, pos))
            pos = i + 1
            continue

        if _is_identifier_start(ch):
            ident_start = pos
            pos += 1
            while pos < length and _is_identifier_part(source[pos]):
                if source[pos] == "-" and pos + 1 < length and source[pos + 1] == ">":
                    break
                pos += 1
            tokens.append(Token("IDENT", source[ident_start:pos], ident_start))
            continue

        matched_punctuation = False
        for kind, text in PUNCTUATION_TOKENS:
            if source.startswith(text, pos):
                tokens.append(Token(kind, text, pos))
                pos += len(text)
                matched_punctuation = True
                break
        if matched_punctuation:
            continue
        raise SyntaxError(f"Unexpected character {source[pos]!r} at {pos}")

    tokens.append(Token("EOF", "", len(source)))
    return tokens


def parse_string_literal(text: str) -> str:
    if text.startswith('"""') and text.endswith('"""') and len(text) >= 6:
        quote = '"'
        content = text[3:-3]
    elif text.startswith("'''") and text.endswith("'''") and len(text) >= 6:
        quote = "'"
        content = text[3:-3]
    elif len(text) >= 2 and text[0] in "\"'" and text[-1] == text[0]:
        quote = text[0]
        content = text[1:-1]
    else:
        raise SyntaxError(f"Invalid string literal: {text!r}")
    out: list[str] = []
    i = 0
    while i < len(content):
        ch = content[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue

        i += 1
        if i >= len(content):
            raise SyntaxError("Trailing backslash in string literal")
        esc = content[i]
        i += 1

        if esc == "n":
            out.append("\n")
        elif esc == "r":
            out.append("\r")
        elif esc == "t":
            out.append("\t")
        elif esc == "\\":
            out.append("\\")
        elif esc == "\"":
            out.append("\"")
        elif esc == "'":
            out.append("'")
        elif esc == "u":
            if i + 4 > len(content):
                raise SyntaxError("Invalid \\u escape in string literal")
            hex_part = content[i:i + 4]
            if not re.fullmatch(r"[0-9A-Fa-f]{4}", hex_part):
                raise SyntaxError("Invalid \\u escape in string literal")
            out.append(chr(int(hex_part, 16)))
            i += 4
        elif esc == quote:
            out.append(quote)
        else:
            raise SyntaxError(f"Unsupported escape sequence: \\{esc}")
    return "".join(out)


def parse_glob_literal(text: str) -> str:
    if not (text.startswith('glob"') and text.endswith('"') and len(text) >= 6):
        raise SyntaxError(f"Invalid glob literal: {text!r}")
    content = text[5:-1]
    out: list[str] = []
    i = 0
    while i < len(content):
        ch = content[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue
        i += 1
        if i >= len(content):
            raise SyntaxError("Invalid glob literal: trailing backslash")
        esc = content[i]
        i += 1
        if esc in {"*", "?", "[", "]", "\\"}:
            out.append("\\" + esc)
            continue
        raise SyntaxError(f"Invalid glob literal escape: \\{esc}")
    return "".join(out)
