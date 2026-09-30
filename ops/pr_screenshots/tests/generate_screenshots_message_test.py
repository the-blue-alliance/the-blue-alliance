import base64
import io
import os

from artifact_data import ARTIFACT_FILENAME, ArtifactData
from generate_screenshots_message import (
    build_rows,
    CommentRow,
    diff_pair,
    generate_message,
    main,
    pair_screenshots,
    ScreenshotPair,
    sibling_filename,
)
from PIL import Image


def _png(color) -> str:
    image = Image.new("RGBA", (4, 4), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


WHITE = _png((255, 255, 255, 255))
BLACK = _png((0, 0, 0, 255))


def test_pair_screenshots_matches_before_to_after_by_name() -> None:
    artifact = ArtifactData(
        pr=1,
        screenshots=[
            ("Homepage", "h-after.png", "a"),
            ("GameDay", "g-after.png", "b"),
        ],
        before_screenshots=[("GameDay", "g-before.png", "c")],
    )

    pairs = pair_screenshots(artifact)

    assert pairs == [
        ScreenshotPair("Homepage", ("Homepage", "h-after.png", "a"), None),
        ScreenshotPair(
            "GameDay",
            ("GameDay", "g-after.png", "b"),
            ("GameDay", "g-before.png", "c"),
        ),
    ]


def test_pair_screenshots_tolerates_an_artifact_from_before_this_change() -> None:
    artifact = ArtifactData(pr=1, screenshots=[("Homepage", "old.png", "a")])

    assert pair_screenshots(artifact)[0].before is None


def test_sibling_filename_swaps_the_phase_or_appends_it() -> None:
    assert sibling_filename("pr-1-gameday-after-2.png", "diff") == (
        "pr-1-gameday-diff-2.png"
    )
    assert sibling_filename("pr-1-http:--localhost:8080-2.png", "diff") == (
        "pr-1-http:--localhost:8080-2-diff.png"
    )


def test_diff_pair_reports_the_change_and_names_the_diff() -> None:
    pair = ScreenshotPair(
        "Homepage",
        ("Homepage", "pr-1-homepage-after-9.png", BLACK),
        ("Homepage", "x", WHITE),
    )

    diff = diff_pair(pair)

    assert diff is not None
    assert diff.filename == "pr-1-homepage-diff-9.png"
    assert diff.changed_fraction == 1.0
    assert Image.open(io.BytesIO(base64.b64decode(diff.image))).size == (4, 4)


def test_diff_pair_without_a_before_is_none() -> None:
    assert diff_pair(ScreenshotPair("H", ("H", "a.png", BLACK), None)) is None


def test_build_rows_uploads_before_after_and_diff() -> None:
    uploaded = []

    def upload(filename: str, image: str) -> str:
        uploaded.append(filename)
        return f"https://x/{filename}"

    rows = build_rows(
        [
            ScreenshotPair(
                "H", ("H", "h-after-1.png", WHITE), ("H", "h-before-1.png", WHITE)
            ),
            ScreenshotPair("G", ("G", "g-after-1.png", BLACK), None),
        ],
        upload,
    )

    assert uploaded == [
        "h-after-1.png",
        "h-before-1.png",
        "h-diff-1.png",
        "g-after-1.png",
    ]
    assert rows == [
        CommentRow(
            "H",
            "https://x/h-after-1.png",
            "https://x/h-before-1.png",
            "https://x/h-diff-1.png",
            0.0,
        ),
        CommentRow("G", "https://x/g-after-1.png"),
    ]


def test_generate_message_renders_a_table_with_the_diff_percentage() -> None:
    message = generate_message(
        [
            CommentRow(
                "Homepage",
                "https://x/a.png",
                "https://x/b.png",
                "https://x/d.png",
                0.0613,
            )
        ]
    )

    assert message.startswith(
        "## Screenshots\n\n| | Before | After | Diff |\n|---|---|---|---|\n"
    )
    assert (
        "| Homepage | ![Homepage before](https://x/b.png) "
        "| ![Homepage after](https://x/a.png) "
        "| ![Homepage diff](https://x/d.png)<br>6.13% of pixels changed |"
    ) in message
    assert "base-branch capture is missing" not in message


def test_generate_message_explains_a_missing_base_capture() -> None:
    message = generate_message(
        [CommentRow("GameDay", "https://x/a.png"), CommentRow("Lost", None)]
    )

    assert (
        "| GameDay | _no base capture_ | ![GameDay after](https://x/a.png) | _n/a_ |"
        in message
    )
    assert "missing for 1 page(s)" in message
    assert "Lost" not in message


def test_main_outside_ci_or_without_artifact_is_a_no_op(
    monkeypatch, tmp_path, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CI", raising=False)
    assert main(["prog", "token"]) == 0
    assert "Only runnable in CI" in capsys.readouterr().out

    monkeypatch.setenv("CI", "true")
    assert main(["prog", "token"]) == 0
    assert f"{ARTIFACT_FILENAME} not found" in capsys.readouterr().out
    assert not os.path.exists("ci_screenshots_message.md")
