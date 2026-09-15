"""
`toolbox hash-files` - computes checksums for every file in a directory and
writes a manifest, e.g. for verifying file integrity in a pipeline.

Standard-library only (hashlib, pathlib).
"""
import hashlib
from pathlib import Path

from toolbox import exit_codes
from toolbox.logging_utils import log


def add_arguments(subparsers) -> None:
    parser = subparsers.add_parser(
        "hash-files",
        help="Compute checksums for every file in a directory and write a manifest.",
        description=(
            "Recursively hashes every file under DIRECTORY and writes a checksums "
            "manifest (default: DIRECTORY/checksums.txt)."
        ),
    )
    parser.add_argument("directory", help="Directory to scan, e.g. /data")
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write the manifest (default: <directory>/checksums.txt)",
    )
    parser.add_argument(
        "--algorithm",
        default="sha256",
        choices=sorted(hashlib.algorithms_guaranteed),
        help="Hash algorithm to use (default: sha256)",
    )
    parser.set_defaults(func=run)


def hash_file(path: Path, algorithm: str = "sha256") -> str:
    """Return the hex digest of a single file, reading it in fixed-size chunks
    so this scales to large files without loading them fully into memory."""
    hasher = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def run(args) -> int:
    directory = Path(args.directory)
    if not directory.is_dir():
        log("ERROR", "Directory not found", directory=str(directory))
        return exit_codes.INPUT_NOT_FOUND

    output_path = Path(args.output) if args.output else directory / "checksums.txt"

    files = sorted(
        p for p in directory.rglob("*")
        if p.is_file() and p.resolve() != output_path.resolve()
    )

    if not files:
        log("WARN", "No files found to hash", directory=str(directory))

    lines = []
    for path in files:
        digest = hash_file(path, args.algorithm)
        rel = path.relative_to(directory)
        lines.append(f"{digest}  {rel}")
        log("INFO", "Hashed file", file=str(rel), algorithm=args.algorithm, digest=digest)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    log("INFO", "Manifest written", output=str(output_path), file_count=len(files))
    return exit_codes.SUCCESS
