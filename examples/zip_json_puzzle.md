# ZIP JSON Puzzle

`examples/zip_json_puzzle.genia` is a small Genia puzzle game built on:

- `zip_read`
- `zip_write`
- `json_parse`
- `json_stringify`
- pipeline debugging helpers such as `trace`

## Puzzle format

The game expects a zip file containing:

- `puzzle.json`
- the input JSON file named by `puzzle.json.input`

Minimal `puzzle.json` shape:

```json
{
  "title": "Normalize Labels",
  "description": "Pull rows, keep labels, trim blanks, uppercase them.",
  "input": "input.json",
  "expected": ["ALPHA", "BETA", "GAMMA"]
}
```

## Run it

```bash
genia examples/zip_json_puzzle.genia puzzle.zip --pipeline 'pick:rows,field:label,trim_each,drop_empty,upper_each'
```

Trace each stage and write a result archive:

```bash
genia examples/zip_json_puzzle.genia puzzle.zip --pipeline 'pick:rows,field:label,trim_each,drop_empty,upper_each' --trace --out solved.zip
```

## Stage vocabulary

- `pick:<key>`
- `field:<key>`
- `trim_each`
- `upper_each`
- `lower_each`
- `drop_empty`
- `reverse`
- `count`

## Result archive

When `--out` is provided the game writes:

- `summary.txt`
- `actual.json` when the pipeline produced a JSON value
- `expected.json`
