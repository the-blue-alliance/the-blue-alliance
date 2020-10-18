import pytest


@pytest.fixture
def setup_full_team(test_data_importer) -> None:
    test_data_importer.import_team(__file__, "data/frc148.json")
    test_data_importer.import_event_list(
        __file__, "data/frc148_events_2019.json", "frc148"
    )
    test_data_importer.import_match_list(__file__, "data/frc148_matches_2019.json")
    test_data_importer.import_media_list(
        __file__, "data/frc148_media_2019.json", 2019, "frc148"
    )
    test_data_importer.import_media_list(
        __file__, "data/frc148_social_media.json", team_key="frc148"
    )
    test_data_importer.import_award_list(__file__, "data/frc148_awards_2019.json")
    test_data_importer.import_district_list(
        __file__, "data/frc148_districts.json", "frc148"
    )
    test_data_importer.import_robot_list(__file__, "data/frc148_robots.json")


@pytest.fixture
def setup_full_event(test_data_importer):
    # So we can import different event keys, return a function

    def import_event(event_key) -> None:
        test_data_importer.import_event(__file__, f"data/{event_key}.json")
        test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")
        test_data_importer.import_event_alliances(
            __file__, f"data/{event_key}_alliances.json", event_key
        )

    return import_event


@pytest.fixture
def setup_full_match(test_data_importer):
    def import_match(match_key) -> None:
        event_key = match_key.split("_")[0]
        test_data_importer.import_event(__file__, f"data/{event_key}.json")
        test_data_importer.import_match(__file__, f"data/{match_key}.json")

    return import_match


@pytest.fixture
def setup_full_year_events(test_data_importer) -> None:
    test_data_importer.import_event_list(__file__, "data/all_events_2019.json")
