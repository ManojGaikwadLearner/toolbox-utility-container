import csv
import json

from toolbox import exit_codes
from toolbox.convert_csv_json import csv_to_json, json_to_csv, run


def _make_args(input_path, output_path, direction=None, indent=2):
    class Args:
        pass

    a = Args()
    a.input = str(input_path)
    a.output = str(output_path)
    a.direction = direction
    a.indent = indent
    return a


def test_csv_to_json_round_trip(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("id,name,completed\n1,Write README,false\n2,Ship it,true\n", encoding="utf-8")
    json_path = tmp_path / "sample.json"

    row_count = csv_to_json(csv_path, json_path)

    assert row_count == 2
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data == [
        {"id": "1", "name": "Write README", "completed": "false"},
        {"id": "2", "name": "Ship it", "completed": "true"},
    ]


def test_json_to_csv_round_trip(tmp_path):
    json_path = tmp_path / "sample.json"
    json_path.write_text(
        json.dumps([{"id": "1", "name": "Write README"}, {"id": "2", "name": "Ship it"}]),
        encoding="utf-8",
    )
    csv_path = tmp_path / "sample.csv"

    row_count = json_to_csv(json_path, csv_path)

    assert row_count == 2
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows == [{"id": "1", "name": "Write README"}, {"id": "2", "name": "Ship it"}]


def test_run_returns_input_not_found_for_missing_file(tmp_path):
    args = _make_args(tmp_path / "missing.csv", tmp_path / "out.json")
    assert run(args) == exit_codes.INPUT_NOT_FOUND


def test_run_returns_parse_error_when_direction_cannot_be_inferred(tmp_path):
    input_path = tmp_path / "sample.txt"
    input_path.write_text("not really csv or json", encoding="utf-8")
    args = _make_args(input_path, tmp_path / "out.dat")
    assert run(args) == exit_codes.PARSE_ERROR


def test_run_succeeds_end_to_end(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("id,name\n1,Test\n", encoding="utf-8")
    json_path = tmp_path / "sample.json"

    args = _make_args(csv_path, json_path)
    assert run(args) == exit_codes.SUCCESS
    assert json.loads(json_path.read_text(encoding="utf-8")) == [{"id": "1", "name": "Test"}]


def test_run_returns_parse_error_on_malformed_json_input(tmp_path):
    json_path = tmp_path / "broken.json"
    json_path.write_text("{not valid json", encoding="utf-8")
    args = _make_args(json_path, tmp_path / "out.csv")
    assert run(args) == exit_codes.PARSE_ERROR
