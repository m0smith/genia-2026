import json
import zipfile
from pathlib import Path

from genia.interpreter import _main


EXAMPLE = Path("examples/zip_json_puzzle.genia")


def _write_puzzle_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "puzzle.json",
            json.dumps(
                {
                    "title": "Normalize Labels",
                    "description": "Pull rows, keep labels, trim blanks, uppercase them.",
                    "input": "input.json",
                    "expected": ["ALPHA", "BETA", "GAMMA"],
                }
            ),
        )
        zf.writestr(
            "input.json",
            json.dumps(
                {
                    "rows": [
                        {"label": " alpha "},
                        {"label": "beta"},
                        {"label": "   "},
                        {"label": "Gamma"},
                    ]
                }
            ),
        )


def test_zip_json_puzzle_briefing_without_pipeline(tmp_path, capsys):
    puzzle_zip = tmp_path / "puzzle.zip"
    _write_puzzle_zip(puzzle_zip)

    exit_code = _main([str(EXAMPLE), str(puzzle_zip)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Normalize Labels" in captured.out
    assert "Use --pipeline" in captured.out
    assert "field:<key>" in captured.out


def test_zip_json_puzzle_passes_and_writes_result_archive(tmp_path, capsys):
    puzzle_zip = tmp_path / "puzzle.zip"
    out_zip = tmp_path / "solved.zip"
    _write_puzzle_zip(puzzle_zip)

    exit_code = _main(
        [
            str(EXAMPLE),
            str(puzzle_zip),
            "--pipeline",
            "pick:rows,field:label,trim_each,drop_empty,upper_each",
            "--trace",
            "--out",
            str(out_zip),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "PASS Normalize Labels" in captured.out
    assert "wrote archive:" in captured.out
    assert "after pick:rows" in captured.err
    assert "after upper_each" in captured.err

    with zipfile.ZipFile(out_zip, "r") as zf:
        assert zf.namelist() == ["summary.txt", "actual.json", "expected.json"]
        assert json.loads(zf.read("actual.json").decode("utf-8")) == ["ALPHA", "BETA", "GAMMA"]
        assert json.loads(zf.read("expected.json").decode("utf-8")) == ["ALPHA", "BETA", "GAMMA"]


def test_zip_json_puzzle_reports_failure_for_wrong_pipeline(tmp_path, capsys):
    puzzle_zip = tmp_path / "puzzle.zip"
    _write_puzzle_zip(puzzle_zip)

    exit_code = _main(
        [
            str(EXAMPLE),
            str(puzzle_zip),
            "--pipeline",
            "pick:rows,field:label,trim_each",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "FAIL Normalize Labels" in captured.out
    assert '"ALPHA"' not in captured.out
    assert '" alpha "' not in captured.out
    assert '\\"alpha\\"' in captured.out
