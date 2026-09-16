import pytest

from toolbox.cli import build_parser


def test_all_subcommands_registered():
    parser = build_parser()
    # argparse exposes subparser choices via the subparsers action
    subparsers_action = next(
        action for action in parser._actions if action.dest == "command"
    )
    registered = set(subparsers_action.choices.keys())
    expected = {"convert-csv-json", "resize-image", "hash-files", "wait-for", "lint-json"}
    assert expected.issubset(registered)


def test_help_exits_cleanly():
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])
    assert exc_info.value.code == 0


def test_missing_command_is_an_error():
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args([])
    assert exc_info.value.code != 0
