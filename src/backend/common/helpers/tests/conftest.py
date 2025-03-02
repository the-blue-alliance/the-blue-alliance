import pytest


@pytest.fixture
def setup_full_event(test_data_importer):
    # So we can import different event keys, return a function

    def import_event(event_key) -> None:
        test_data_importer.import_event(__file__, f"data/{event_key}.json")
        test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")
        test_data_importer.import_event_alliances(
            __file__, f"data/{event_key}_alliances.json", event_key
        )
        test_data_importer.import_event_teams(
            __file__, f"data/{event_key}_teams.json", event_key
        )
        test_data_importer.import_event_rankings(
            __file__, f"data/{event_key}_rankings.json", event_key
        )
        test_data_importer.import_award_list(__file__, f"data/{event_key}_awards.json")
        test_data_importer.import_event_district_points(
            __file__, f"data/{event_key}_district_points.json", event_key
        )
        test_data_importer.maybe_import_event_regional_champs_pool_points(
            __file__, f"data/{event_key}_regional_champs_pool_points.json", event_key
        )

    return import_event
