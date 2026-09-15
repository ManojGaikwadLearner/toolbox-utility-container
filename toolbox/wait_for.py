"""
`toolbox wait-for` - blocks until a TCP host:port becomes reachable, or fails
after a timeout.

This is the classic "wait for the database to be ready" pattern used in
CI/CD pipelines and as a workaround for Compose's `depends_on`, which only
waits for a container to *start*, not for the service inside it to actually
be accepting connections. Standard-library only (socket, time).
"""
import socket
import time

from toolbox import exit_codes
from toolbox.logging_utils import log


def add_arguments(subparsers) -> None:
    parser = subparsers.add_parser(
        "wait-for",
        help="Block until a host:port becomes reachable, or fail after a timeout.",
        description=(
            "Polls a TCP host:port until a connection succeeds or the timeout "
            "elapses. Exit code 0 means the target became reachable; exit code 1 "
            "means it timed out. Designed for orchestration, e.g. an app entrypoint "
            "waiting on a database before starting."
        ),
    )
    parser.add_argument("target", help="Target as host:port, e.g. db:5432")
    parser.add_argument(
        "--timeout", type=float, default=30.0,
        help="Total seconds to wait before giving up (default: 30)",
    )
    parser.add_argument(
        "--interval", type=float, default=1.0,
        help="Seconds to sleep between connection attempts (default: 1)",
    )
    parser.set_defaults(func=run)


def parse_target(target: str):
    if ":" not in target:
        raise ValueError(f"Target must be in host:port form, got: {target!r}")
    host, port_str = target.rsplit(":", 1)
    if not host or not port_str.isdigit():
        raise ValueError(f"Target must be in host:port form, got: {target!r}")
    return host, int(port_str)


def is_reachable(host: str, port: int, connect_timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=connect_timeout):
            return True
    except OSError:
        return False


def run(args) -> int:
    try:
        host, port = parse_target(args.target)
    except ValueError as exc:
        log("ERROR", "Invalid target", target=args.target, error=str(exc))
        return exit_codes.PARSE_ERROR

    log("INFO", "Waiting for target to become reachable", host=host, port=port, timeout=args.timeout)

    deadline = time.monotonic() + args.timeout
    attempt = 0
    connect_timeout = min(args.interval, 5.0) or 1.0

    while True:
        attempt += 1
        if is_reachable(host, port, connect_timeout):
            log("INFO", "Target is reachable", host=host, port=port, attempts=attempt)
            return exit_codes.SUCCESS

        if time.monotonic() >= deadline:
            log(
                "ERROR", "Timed out waiting for target",
                host=host, port=port, timeout=args.timeout, attempts=attempt,
            )
            return exit_codes.TIMEOUT

        log("INFO", "Target not yet reachable, retrying", host=host, port=port, attempt=attempt)
        time.sleep(args.interval)
