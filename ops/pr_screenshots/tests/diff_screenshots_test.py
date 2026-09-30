from diff_screenshots import diff_images, HIGHLIGHT, main
from PIL import Image


def _solid(size, color=(200, 200, 200, 255)):
    return Image.new("RGBA", size, color)


def test_identical_images_have_no_changed_pixels() -> None:
    result = diff_images(_solid((10, 8)), _solid((10, 8)))

    assert result.changed_pixels == 0
    assert result.total_pixels == 80
    assert result.changed_fraction == 0.0
    assert result.image.size == (10, 8)


def test_changed_pixels_are_painted_red_and_counted() -> None:
    after = _solid((10, 8))
    after.putpixel((3, 4), (0, 0, 0, 255))
    after.putpixel((7, 1), (0, 0, 0, 255))

    result = diff_images(_solid((10, 8)), after)

    assert result.changed_pixels == 2
    assert result.changed_fraction == 2 / 80
    assert result.image.getpixel((3, 4)) == HIGHLIGHT
    assert result.image.getpixel((7, 1)) == HIGHLIGHT
    assert result.image.getpixel((0, 0)) != HIGHLIGHT


def test_subthreshold_noise_is_ignored() -> None:
    after = _solid((4, 4))
    after.putpixel((1, 1), (210, 205, 195, 255))  # within THRESHOLD of the base

    assert diff_images(_solid((4, 4)), after).changed_pixels == 0


def test_size_mismatch_pads_to_the_larger_and_counts_padding() -> None:
    before = _solid((10, 8))
    after = _solid((10, 10))  # two extra rows, same content otherwise

    result = diff_images(before, after)

    assert result.image.size == (10, 10)
    assert result.total_pixels == 100
    assert result.changed_pixels == 20
    assert result.image.getpixel((0, 9)) == HIGHLIGHT
    assert result.image.getpixel((0, 0)) != HIGHLIGHT


def test_main_writes_the_diff_and_reports_the_percentage(tmp_path, capsys) -> None:
    before = tmp_path / "before.png"
    after = tmp_path / "after.png"
    out = tmp_path / "diff.png"
    _solid((10, 10)).save(before)
    changed = _solid((10, 10))
    changed.putpixel((0, 0), (0, 0, 0, 255))
    changed.save(after)

    assert main(["diff_screenshots.py", str(before), str(after), str(out)]) == 0

    assert Image.open(out).getpixel((0, 0)) == HIGHLIGHT
    assert "1 of 100 pixels changed (1.00%)" in capsys.readouterr().out


def test_main_rejects_wrong_arity(capsys) -> None:
    assert main(["diff_screenshots.py", "only-one.png"]) == 2
    assert (
        "diff_screenshots.py before.png after.png diff.png" in capsys.readouterr().err
    )
