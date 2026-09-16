import pytest

pytest.importorskip("PIL")

from PIL import Image  # noqa: E402

from toolbox import exit_codes  # noqa: E402
from toolbox.resize_image import run  # noqa: E402


def _make_args(in_dir, out_dir, max_dimension=100, quality=85):
    class Args:
        pass

    a = Args()
    a.in_dir = str(in_dir)
    a.out_dir = str(out_dir)
    a.max_dimension = max_dimension
    a.quality = quality
    return a


def _make_test_image(path, size=(400, 200), color=(255, 0, 0)):
    Image.new("RGB", size, color).save(path)


def test_run_resizes_images_within_max_dimension(tmp_path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    _make_test_image(in_dir / "photo.png", size=(400, 200))

    args = _make_args(in_dir, out_dir, max_dimension=100)
    assert run(args) == exit_codes.SUCCESS

    with Image.open(out_dir / "photo.png") as img:
        assert max(img.size) <= 100
        # Aspect ratio (2:1) should be preserved
        assert img.size[0] == 2 * img.size[1]


def test_run_returns_input_not_found_for_missing_directory(tmp_path):
    args = _make_args(tmp_path / "missing", tmp_path / "out")
    assert run(args) == exit_codes.INPUT_NOT_FOUND


def test_run_ignores_non_image_files(tmp_path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    (in_dir / "notes.txt").write_text("not an image", encoding="utf-8")
    _make_test_image(in_dir / "photo.jpg", size=(300, 300))

    args = _make_args(in_dir, out_dir)
    assert run(args) == exit_codes.SUCCESS
    assert (out_dir / "photo.jpg").exists()
    assert not (out_dir / "notes.txt").exists()
