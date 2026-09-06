from backend.tasks_io.datafeeds.parsers.first.resource_library_parser import (
    ResourceLibraryParser,
)


def _parse(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/hall_of_fame.html")
    with open(path, "rb") as f:
        return ResourceLibraryParser().parse(f.read())


def test_parses_all_winner_entries(test_data_importer) -> None:
    teams, more = _parse(test_data_importer)

    assert more is False
    assert {t["year"] for t in teams} == {2024, 2021, 2019, 1993}


def test_impact_era_entry(test_data_importer) -> None:
    teams, _ = _parse(test_data_importer)
    team = next(t for t in teams if t["year"] == 2024)

    assert team["team_id"] == "frc2486"
    assert team["team_number"] == 2486
    assert team["video"] == "9oBL8s2Y7tA"
    assert team["presentation"] == "TIFLhevHf7k"
    assert (
        team["essay"]
        == "https://www.firstinspires.org/hubfs/web/program/frc/awards/fia-essays/2024/2486.pdf?hsLang=en"
    )


def test_chairmans_era_entry(test_data_importer) -> None:
    teams, _ = _parse(test_data_importer)
    team = next(t for t in teams if t["year"] == 2021)

    assert team["team_id"] == "frc503"
    assert team["video"] == "34gb_BMgnw8"
    assert team["presentation"] == "_o9urZ-pkxw"
    assert team["essay"].endswith("2021/503.pdf?hsLang=en")


def test_non_youtube_presentation_is_dropped(test_data_importer) -> None:
    teams, _ = _parse(test_data_importer)
    team = next(t for t in teams if t["year"] == 2019)

    assert team["presentation"] is None
    assert team["essay"].endswith("2019/1816.pdf?hsLang=en")


def test_entry_without_materials(test_data_importer) -> None:
    teams, _ = _parse(test_data_importer)
    team = next(t for t in teams if t["year"] == 1993)

    assert team["team_id"] == "frc7"
    assert team["video"] is None
    assert team["presentation"] is None
    assert team["essay"] is None


def test_no_details_returns_empty() -> None:
    teams, more = ResourceLibraryParser().parse(b"<html><body>nope</body></html>")

    assert teams == []
    assert more is False
