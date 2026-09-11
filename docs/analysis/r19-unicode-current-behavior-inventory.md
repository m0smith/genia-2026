# R19 Unicode Current-Behavior Inventory

Status: **Planning analysis — non-authoritative.** `GENIA_STATE.md` remains final authority for implemented behavior.

This inventory records the Python reference-host behavior R19 must either preserve explicitly or replace with an approved portable contract. It does not change runtime behavior.

## Current implementation facts

The Python reference host centralizes several string helpers in `src/genia/utf8.py`:

- `utf8_byte_length(s)` encodes the Python `str` as UTF-8 and returns byte length.
- `utf8_is_boundary(s, byte_offset)` encodes to UTF-8, rejects offsets outside `[0, byte_length]`, treats both endpoints as boundaries, and otherwise rejects continuation-byte offsets.
- `utf8_codepoints(s)` returns `iter(s)` and therefore inherits Python `str` iteration semantics.
- `utf8_safe_slice_by_codepoint(s, start, end)` delegates directly to Python slicing.
- `format_display` returns ordinary strings unchanged.
- `format_debug` wraps strings in double quotes and escapes backslash, double quote, newline, carriage return, and tab. Other Unicode code points are emitted literally.

These are useful reference-host facts, but Python `str` is not itself a portable Genia contract.

## Inventory matrix

| Surface | Python reference-host behavior today | Portable status before R19 | R19 contract question |
|---|---|---|---|
| Public string unit | Python Unicode `str` | implicit/underspecified | Define Genia string as Unicode scalar/code-point sequence or another exact model. |
| Iteration | Python `str` iteration, one code point per element in normal Python scalar-value model | implicit | Specify unit and ordering independently of Python. |
| Code-point slicing | Python slice semantics including negative indices, omitted bounds, and clamping | implicit | Decide which slice rules are portable and whether negative bounds are part of contract. |
| UTF-8 byte length | `len(s.encode("utf-8"))` | implementation fact | Make exact UTF-8 byte-count semantics explicit. |
| UTF-8 boundary check | encoded-byte continuation-bit test; endpoints valid | implementation fact | Define valid domain, endpoint behavior, and misuse/non-boundary results. |
| Invalid UTF-8 input | ordinary Genia strings are already Python `str`; malformed byte sequences only arise at byte/host decode boundaries | not centrally defined | Specify decoding failure behavior at boundaries that produce strings from bytes. |
| Display rendering | raw string contents, no quoting/escaping | implemented but host-independent rule not isolated | Decide whether this remains exact portable display behavior. |
| Debug rendering | double quotes plus escapes for `\\`, `"`, `\n`, `\r`, `\t`; other Unicode emitted literally | implemented, partially explicit in code only | Define exact escaping, including controls outside the five current cases. |
| Unicode normalization | no explicit normalization step in `utf8.py`; Python preserves code-point sequence supplied | not documented as language rule | Decide whether Genia guarantees no implicit normalization. |
| Grapheme clusters | no grapheme-cluster abstraction in current helpers | not implemented | Keep out of R19 unless an existing surface already promises it. |
| Locale-sensitive collation/casing | no R19 roadmap requirement and no portable contract identified in this inventory | not implemented/irrelevant | Explicit non-goal for R19. |

## Cross-surface observations

### Formatting

The format engine uses Python string length/slicing for width and precision-style string formatting. This means width/truncation currently follows Python code-point indexing rather than byte counts or grapheme clusters. R19 must either contract that behavior or explicitly classify those format-spec details outside the first Unicode portability slice.

### Configuration and external text

Existing configuration features already contain narrow UTF-8 behavior (for example `.env` parsing), but R19 should not broaden those features. It should define the portable string/UTF-8 boundary they consume.

### Equality

R18 owns value equality. R19 must not introduce Unicode-normalization-equivalent equality. If two strings contain different code-point sequences, R19 must not silently make them equal through normalization unless R18 is explicitly revised through its own contract gate.

## Recommended contract decisions to resolve in E19-0

The draft R19 contract should make the following explicit, subject to approval:

1. Genia strings are sequences of Unicode scalar values/code points, not UTF-8 bytes and not grapheme clusters.
2. UTF-8 is the portable byte encoding at explicit encode/decode boundaries.
3. String iteration and slicing operate on code points.
4. No implicit Unicode normalization occurs.
5. UTF-8 byte boundary queries operate over the UTF-8 encoding of the string and never split a code point.
6. Debug escaping is Genia-defined rather than delegated to host `repr` behavior.
7. Invalid UTF-8 at an explicit decode boundary yields one deterministic portable failure rather than host exception text.

## Required future shared evidence

Candidate edge cases for later R19 test slices:

- ASCII
- Latin-1 supplement / non-ASCII BMP
- supplementary-plane character (for example one emoji code point)
- combining-sequence text showing code-point rather than grapheme behavior
- code-point slicing with omitted, positive, negative, and out-of-range bounds if negative/clamping behavior is approved
- UTF-8 byte lengths for 1/2/3/4-byte code points
- byte-boundary true/false cases inside multi-byte encodings
- debug escaping for quote, backslash, newline, carriage return, tab, and any additional approved control escaping
- malformed UTF-8 at an explicit byte-to-string boundary

## Non-goals of this inventory

- no runtime changes
- no new string syntax
- no grapheme-cluster API
- no normalization API
- no locale/collation contract
- no C++ implementation
