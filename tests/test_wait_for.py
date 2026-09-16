import socket
import threading

from toolbox import exit_codes
from toolbox.wait_for import parse_target, run


def _make_args(target, timeout=3.0, interval=0.2):
    class Args:
        pass

    a = Args()
    a.target = target
    a.timeout = timeout
    a.interval = interval
    return a


def test_parse_target_valid():
    assert parse_target("db:5432") == ("db", 5432)
    assert parse_target("127.0.0.1:8000") == ("127.0.0.1", 8000)


def test_parse_target_rejects_missing_port():
    try:
        parse_target("db")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_run_returns_parse_error_for_invalid_target():
    args = _make_args("not-a-valid-target")
    assert run(args) == exit_codes.PARSE_ERROR


def test_run_returns_timeout_for_unreachable_port():
    # Port 1 is reserved and essentially never has anything listening;
    # a short timeout keeps this test fast.
    args = _make_args("127.0.0.1:1", timeout=1.0, interval=0.2)
    assert run(args) == exit_codes.TIMEOUT


def test_run_returns_success_for_reachable_port():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]

    stop = threading.Event()

    def accept_loop():
        server.settimeout(0.5)
        while not stop.is_set():
            try:
                conn, _ = server.accept()
                conn.close()
            except socket.timeout:
                continue

    thread = threading.Thread(target=accept_loop, daemon=True)
    thread.start()

    try:
        args = _make_args(f"127.0.0.1:{port}", timeout=5.0, interval=0.2)
        assert run(args) == exit_codes.SUCCESS
    finally:
        stop.set()
        thread.join(timeout=2)
        server.close()
