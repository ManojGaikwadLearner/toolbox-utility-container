import json

import pytest

pytest.importorskip("jsonschema")

from toolbox import exit_codes  # noqa: E402
from toolbox.lint_json import run  # noqa: E402

SCHEMA = {
    "type": "object",
    "required": ["id", "name", "completed"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string", "minLength": 1},
        "completed": {"type": "boolean"},
    },
    "additionalProperties": False,
}


def _make_args(directory, schema_path):
    class Args:
        pass

    a = Args()
    a.directory = str(directory)
    a.schema = str(schema_path)
    return a


def _write_schema(tmp_path):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(SCHEMA), encoding="utf-8")
    return schema_path


def test_run_passes_when_all_files_are_valid(tmp_path):
    schema_path = _write_schema(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "valid.json").write_text(
        json.dumps({"id": 1, "name": "Write README", "completed": False}), encoding="utf-8"
    )

    args = _make_args(data_dir, schema_path)
    assert run(args) == exit_codes.SUCCESS


def test_run_fails_when_a_file_violates_the_schema(tmp_path):
    schema_path = _write_schema(tmp_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "valid.json").write_text(
        json.dumps({"id": 1, "name": "Write README", "completed": False}), encoding="utf-8"
    )
    (data_dir / "invalid.json").write_text(
        json.dumps({"id": "not-a-number", "name": ""}), encoding="utf-8"
    )

    args = _make_args(data_dir, schema_path)
    assert run(args) == exit_codes.VALIDATION_FAILED


def test_run_returns_input_not_found_for_missing_directory(tmp_path):
    schema_path = _write_schema(tmp_path)
    args = _make_args(tmp_path / "missing", schema_path)
    assert run(args) == exit_codes.INPUT_NOT_FOUND


def test_run_returns_input_not_found_for_missing_schema(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    args = _make_args(data_dir, tmp_path / "missing-schema.json")
    assert run(args) == exit_codes.INPUT_NOT_FOUND
