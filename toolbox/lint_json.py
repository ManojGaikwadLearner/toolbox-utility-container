"""
`toolbox lint-json` - validates every .json file in a directory against a
JSON Schema, exiting non-zero if any file is invalid. Meant to be dropped
into a CI pipeline as a data-quality gate.

Requires the `jsonschema` package (declared in pyproject.toml / requirements.txt).
"""
import json
from pathlib import Path

from toolbox import exit_codes
from toolbox.logging_utils import log

try:
    import jsonschema
except ImportError:  # pragma: no cover - exercised only in environments missing the dep
    jsonschema = None


def add_arguments(subparsers) -> None:
    parser = subparsers.add_parser(
        "lint-json",
        help="Validate every .json file in a directory against a JSON Schema.",
        description=(
            "Validates every *.json file under DIRECTORY against SCHEMA. Exits "
            "non-zero if any file fails validation, so it can act as a CI "
            "quality gate rather than just a reporting tool."
        ),
    )
    parser.add_argument("directory", help="Directory containing .json files to validate, e.g. /data")
    parser.add_argument("--schema", required=True, help="Path to the JSON Schema file")
    parser.set_defaults(func=run)


def validate_file(path: Path, validator) -> list:
    """Return a list of human-readable error strings; empty list means valid."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]

    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    return [
        f"{'/'.join(str(p) for p in error.path) or '<root>'}: {error.message}"
        for error in errors
    ]


def run(args) -> int:
    if jsonschema is None:
        log("ERROR", "The 'jsonschema' package is not installed")
        return exit_codes.GENERIC_ERROR

    directory = Path(args.directory)
    schema_path = Path(args.schema)

    if not directory.is_dir():
        log("ERROR", "Directory not found", directory=str(directory))
        return exit_codes.INPUT_NOT_FOUND
    if not schema_path.is_file():
        log("ERROR", "Schema file not found", schema=str(schema_path))
        return exit_codes.INPUT_NOT_FOUND

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log("ERROR", "Schema file is not valid JSON", schema=str(schema_path), error=str(exc))
        return exit_codes.PARSE_ERROR

    validator = jsonschema.Draft7Validator(schema)
    json_files = sorted(directory.rglob("*.json"))

    if not json_files:
        log("WARN", "No .json files found to validate", directory=str(directory))

    failed = 0
    for path in json_files:
        errors = validate_file(path, validator)
        if errors:
            failed += 1
            log("FAIL", "Schema validation failed", file=str(path), errors="; ".join(errors))
        else:
            log("PASS", "Schema validation passed", file=str(path))

    if failed:
        log("ERROR", "Lint failed", failed=failed, total=len(json_files))
        return exit_codes.VALIDATION_FAILED

    log("INFO", "All files passed schema validation", total=len(json_files))
    return exit_codes.SUCCESS
