"""
Structured logging for a container that has no other observability story.

A utility container's only real output channels are stdout and its exit
code (see README). Every subcommand routes its progress and errors through
this single `log()` function so `docker logs`, or a CI log viewer, gets
consistent, greppable, machine-parseable lines instead of ad-hoc print()
statements with inconsistent formatting.
"""
import json
from datetime import datetime, timezone


def log(level: str, message: str, **fields) -> None:
    """Print one JSON object per line to stdout.

    Example output:
        {"ts": "2026-09-15T10:03:21+00:00", "level": "INFO", "msg": "Hashed file", "file": "sample.csv", "digest": "..."}
    """
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "level": level,
        "msg": message,
    }
    record.update(fields)
    print(json.dumps(record), flush=True)
