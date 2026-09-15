"""
`toolbox resize-image` - batch-resizes/compresses every image in a directory.

Requires Pillow (declared in pyproject.toml / requirements.txt).
"""
from pathlib import Path

from toolbox import exit_codes
from toolbox.logging_utils import log

try:
    from PIL import Image
except ImportError:  # pragma: no cover - exercised only in environments missing the dep
    Image = None

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff"}


def add_arguments(subparsers) -> None:
    parser = subparsers.add_parser(
        "resize-image",
        help="Batch-resize/compress every image in a directory.",
        description=(
            "Resizes every supported image file in --in-dir (preserving aspect "
            "ratio, capped at --max-dimension) and writes the results to --out-dir "
            "under the same filenames."
        ),
    )
    parser.add_argument("--in-dir", required=True, help="Directory of source images, e.g. /data/in")
    parser.add_argument("--out-dir", required=True, help="Directory to write resized images, e.g. /data/out")
    parser.add_argument(
        "--max-dimension", type=int, default=800,
        help="Max width/height in pixels; aspect ratio is preserved (default: 800)",
    )
    parser.add_argument(
        "--quality", type=int, default=85,
        help="JPEG/WebP quality, 1-95 (default: 85); ignored for lossless formats like PNG",
    )
    parser.set_defaults(func=run)


def resize_one(src: Path, dst: Path, max_dimension: int, quality: int) -> None:
    with Image.open(src) as img:
        if src.suffix.lower() in (".jpg", ".jpeg") and img.mode in ("P", "RGBA"):
            img = img.convert("RGB")
        img.thumbnail((max_dimension, max_dimension))

        save_kwargs = {}
        if src.suffix.lower() in (".jpg", ".jpeg", ".webp"):
            save_kwargs["quality"] = quality

        dst.parent.mkdir(parents=True, exist_ok=True)
        img.save(dst, **save_kwargs)


def run(args) -> int:
    if Image is None:
        log("ERROR", "Pillow is not installed")
        return exit_codes.GENERIC_ERROR

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)

    if not in_dir.is_dir():
        log("ERROR", "Input directory not found", directory=str(in_dir))
        return exit_codes.INPUT_NOT_FOUND

    out_dir.mkdir(parents=True, exist_ok=True)

    images = sorted(
        p for p in in_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not images:
        log("WARN", "No supported images found", directory=str(in_dir))

    processed, failed = 0, 0
    for src in images:
        dst = out_dir / src.name
        try:
            resize_one(src, dst, args.max_dimension, args.quality)
            processed += 1
            log("INFO", "Resized image", file=src.name, output=str(dst))
        except Exception as exc:  # noqa: BLE001 - genuinely want to catch/report any Pillow failure
            failed += 1
            log("FAIL", "Failed to process image", file=src.name, error=str(exc))

    log("INFO", "Batch resize complete", processed=processed, failed=failed, total=len(images))

    if failed and processed:
        return exit_codes.PARTIAL_FAILURE
    if failed and not processed:
        return exit_codes.PARSE_ERROR
    return exit_codes.SUCCESS
