import hashlib

from toolbox import exit_codes
from toolbox.hash_files import hash_file, run


def _make_args(directory, output=None, algorithm="sha256"):
    class Args:
        pass

    a = Args()
    a.directory = str(directory)
    a.output = str(output) if output else None
    a.algorithm = algorithm
    return a


def test_hash_file_matches_hashlib_directly(tmp_path):
    file_path = tmp_path / "hello.txt"
    file_path.write_bytes(b"hello world")

    expected = hashlib.sha256(b"hello world").hexdigest()
    assert hash_file(file_path, "sha256") == expected


def test_run_returns_input_not_found_for_missing_directory(tmp_path):
    args = _make_args(tmp_path / "does-not-exist")
    assert run(args) == exit_codes.INPUT_NOT_FOUND


def test_run_writes_manifest_with_correct_digests(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"content a")
    (tmp_path / "b.txt").write_bytes(b"content b")

    args = _make_args(tmp_path)
    assert run(args) == exit_codes.SUCCESS

    manifest = (tmp_path / "checksums.txt").read_text(encoding="utf-8")
    lines = {line.split("  ")[1]: line.split("  ")[0] for line in manifest.strip().splitlines()}

    assert lines["a.txt"] == hashlib.sha256(b"content a").hexdigest()
    assert lines["b.txt"] == hashlib.sha256(b"content b").hexdigest()


def test_run_manifest_excludes_itself_from_hashing(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"content a")
    args = _make_args(tmp_path)
    run(args)
    # Run again - the previously-written checksums.txt should not be hashed
    # (and thus not appear as an entry inside itself).
    run(args)
    manifest = (tmp_path / "checksums.txt").read_text(encoding="utf-8")
    assert "checksums.txt" not in manifest


def test_run_with_custom_output_path(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"content a")
    output_path = tmp_path / "manifest.txt"

    args = _make_args(tmp_path, output=output_path)
    assert run(args) == exit_codes.SUCCESS
    assert output_path.exists()
