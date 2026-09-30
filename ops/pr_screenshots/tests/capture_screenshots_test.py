import base64
import os
import pickle
import subprocess

import capture_screenshots as module
from artifact_data import ARTIFACT_FILENAME, ArtifactData
from capture_screenshots import (
    capture_screenshots,
    main,
    screenshot_filename,
    with_before_screenshots,
)


def test_screenshot_filename_slugs_the_name_and_carries_the_phase() -> None:
    assert screenshot_filename(123, "GameDay", "after", 42) == (
        "pr-123-gameday-after-42.png"
    )
    assert screenshot_filename(7, "Team 254 / 2026", "before", 1) == (
        "pr-7-team-254-2026-before-1.png"
    )


def test_capture_screenshots_encodes_each_page() -> None:
    shots = capture_screenshots(
        [("Homepage", "http://x/"), ("GameDay", "http://x/gameday")],
        "after",
        pr=5,
        capture=lambda url: url.encode(),
        now=lambda: 99,
    )

    assert shots == [
        (
            "Homepage",
            "pr-5-homepage-after-99.png",
            base64.b64encode(b"http://x/").decode(),
        ),
        (
            "GameDay",
            "pr-5-gameday-after-99.png",
            base64.b64encode(b"http://x/gameday").decode(),
        ),
    ]


def test_capture_screenshots_skips_a_page_whose_capture_fails() -> None:
    def capture(url: str) -> bytes:
        if "gameday" in url:
            raise subprocess.CalledProcessError(1, "capture-website")
        return b"png"

    shots = capture_screenshots(
        [("Homepage", "http://x/"), ("GameDay", "http://x/gameday")],
        "after",
        pr=5,
        capture=capture,
        now=lambda: 0,
    )

    assert [name for name, _, _ in shots] == ["Homepage"]


def test_with_before_screenshots_keeps_the_head_capture_intact() -> None:
    head = ArtifactData(pr=1, screenshots=[("Homepage", "a.png", "aaa")])

    merged = with_before_screenshots(head, [("Homepage", "b.png", "bbb")])

    assert merged["pr"] == 1
    assert merged["screenshots"] == [("Homepage", "a.png", "aaa")]
    assert merged["before_screenshots"] == [("Homepage", "b.png", "bbb")]
    assert "before_screenshots" not in head


def test_main_outside_ci_does_nothing(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.chdir(tmp_path)

    assert main([]) == 0

    assert "Only runnable in CI" in capsys.readouterr().out
    assert not os.path.exists(ARTIFACT_FILENAME)


def test_main_head_then_base_builds_one_artifact(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CI", "true")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "GITHUB_PULL_REQUEST_NUMBER", 321)
    monkeypatch.setattr(module, "_capture_website", lambda url: url.encode())
    monkeypatch.setattr(module, "CAPTURE_URLS", [("Homepage", "http://x/")])

    assert main([]) == 0
    assert main(["--before"]) == 0

    with open(ARTIFACT_FILENAME, "rb") as f:
        artifact = pickle.load(f)
    assert artifact["pr"] == 321
    assert [s[0] for s in artifact["screenshots"]] == ["Homepage"]
    assert [s[0] for s in artifact["before_screenshots"]] == ["Homepage"]
    assert "-after-" in artifact["screenshots"][0][1]
    assert "-before-" in artifact["before_screenshots"][0][1]
