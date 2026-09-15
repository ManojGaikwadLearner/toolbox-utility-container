"""
`toolbox convert-csv-json` - converts a CSV file to JSON, or a JSON array of
objects back to CSV.

Uses only the standard library (csv, json) - no external dependency needed
for this one, which keeps its unit tests runnable anywhere.
"""
import csv
import json
from pathlib import Path

from toolbox import exit_codes
from toolbox.logging_utils import log


def add_arguments(subparsers) -> None:
    parser = subparsers.add_parser(
        "convert-csv-json",
        help="Convert a CSV file to JSON, or a JSON array of objects to CSV.",
        description=(
            "Converts between CSV and JSON. Direction is inferred from the "
            "input/output file extensions unless --direction is given explicitly. "
            "Reads INPUT and writes OUTPUT - typically both inside a mounted volume, "
            "e.g. /data/in/sample.csv and /data/out/sample.json."
        ),
    )
    parser.add_argument("input", help="Path to the input file (.csv or .json)")
    parser.add_argument("output", help="Path to write the converted file")
    parser.add_argument(
        "--direction",
        choices=["csv2json", "json2csv"],
        default=None,
        help="Force the conversion direction instead of inferring it from file extensions",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentation level for JSON output (default: 2)",
    )
    parser.set_defaults(func=run)


def _infer_direction(input_path: Path, output_path: Path, explicit):
    if explicit:
        return explicit
    in_ext = input_path.suffix.lower()
    out_ext = output_path.suffix.lower()
    if in_ext == ".csv" and out_ext == ".json":
        return "csv2json"
    if in_ext == ".json" and out_ext == ".csv":
        return "json2csv"
    return None


def csv_to_json(input_path: Path, output_path: Path, indent: int = 2) -> int:
    """Convert a CSV file to a JSON array of objects. Returns the row count."""
    with input_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=indent)
        f.write("\n")
    return len(rows)


def json_to_csv(input_path: Path, output_path: Path) -> int:
    """Convert a JSON array of flat objects to CSV. Returns the row count."""
    with input_path.open(encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or (data and not all(isinstance(row, dict) for row in data)):
        raise ValueError("Expected JSON input to be an array of objects")

    fieldnames = list(data[0].keys()) if data else []
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return len(data)


def run(args) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        log("ERROR", "Input file not found", input=str(input_path))
        return exit_codes.INPUT_NOT_FOUND

    direction = _infer_direction(input_path, output_path, args.direction)
    if direction is None:
        log(
            "ERROR",
            "Could not infer conversion direction from file extensions; pass --direction explicitly",
            input=str(input_path),
            output=str(output_path),
        )
        return exit_codes.PARSE_ERROR

    log("INFO", "Starting conversion", direction=direction, input=str(input_path), output=str(output_path))

    try:
        if direction == "csv2json":
            row_count = csv_to_json(input_path, output_path, args.indent)
        else:
            row_count = json_to_csv(input_path, output_path)
    except (OSError, ValueError, json.JSONDecodeError, csv.Error) as exc:
        log("ERROR", "Conversion failed", input=str(input_path), error=str(exc))
        return exit_codes.PARSE_ERROR

    log("INFO", "Conversion complete", direction=direction, output=str(output_path), rows=row_count)
    return exit_codes.SUCCESS
