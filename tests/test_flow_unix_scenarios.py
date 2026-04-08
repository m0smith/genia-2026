from genia.interpreter import _main


class CountingStdin:
    def __init__(self, lines: list[str]):
        self._lines = list(lines)
        self.reads = 0
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._lines):
            raise StopIteration
        self.reads += 1
        value = self._lines[self._index]
        self._index += 1
        return value


def test_unix_pipe_prints_trimmed_non_blank_lines(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["  alpha  \n", "\n", " beta\n"]))

    exit_code = _main(["-p", 'map(trim) |> filter((line) -> line != "") |> each(print)'])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "alpha\nbeta\n"
    assert captured.err == ""


def test_unix_pipe_option_aware_line_transform_uses_explicit_helpers(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["10\n", "oops\n", "20\n"]))

    exit_code = _main(
        [
            "-p",
            'map((row) -> unwrap_or("bad", row |> parse_int |> flat_map_some((n) -> some(n + 1)))) |> each(print)',
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "11\nbad\n21\n"
    assert captured.err == ""


def test_unix_command_mode_sums_structured_rows_with_rules(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.stdin",
        CountingStdin(["a b c d 5 x\n", "1 2 3 4 6 y\n", "short\n"]),
    )

    exit_code = _main(
        [
            "-c",
            'stdin |> lines |> rules((r, _) -> split_whitespace(r) |> nth(4) |> flat_map_some(parse_int) |> flat_map_some(rule_emit)) |> collect |> sum',
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "11"
    assert captured.err == ""


def test_unix_pipe_head_stops_after_first_line(monkeypatch, capsys):
    stdin = CountingStdin(["first\n", "second\n", "third\n"])
    monkeypatch.setattr("sys.stdin", stdin)

    exit_code = _main(["-p", "head(1) |> each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "first\n"
    assert captured.err == ""
    assert stdin.reads == 1


def test_unix_pipe_empty_input_is_clean(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin([]))

    exit_code = _main(["-p", "map(trim) |> each(print)"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_unix_pipe_collect_alone_explains_stage_only_model(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", CountingStdin(["a\n", "b\n"]))

    exit_code = _main(["-p", "collect"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert (
        captured.err.strip()
        == "Error: Pipe mode stage expression must produce a flow for the automatic final run; received list"
    )
