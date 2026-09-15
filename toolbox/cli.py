"""
The `toolbox` CLI - a single multi-purpose entrypoint with one subcommand per
utility. This is what the Docker image's ENTRYPOINT points at, so the image
behaves like a native binary: `docker run --rm toolbox-container hash-files /data`.
"""
import argparse
import sys

from toolbox import convert_csv_json, hash_files, lint_json, resize_image, wait_for


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="toolbox",
        description=(
            "A multi-purpose utility container CLI: one image, several genuine, "
            "single-purpose, ephemeral commands. Each subcommand runs, does its "
            "job, and exits with a meaningful code - there is no long-running "
            "process here."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_csv_json.add_arguments(subparsers)
    resize_image.add_arguments(subparsers)
    hash_files.add_arguments(subparsers)
    wait_for.add_arguments(subparsers)
    lint_json.add_arguments(subparsers)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
