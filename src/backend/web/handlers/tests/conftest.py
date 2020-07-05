import pytest
from werkzeug.test import Client


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    pass


@pytest.fixture
def web_client() -> Client:
    from backend.web.main import app

    return app.test_client()


@pytest.fixture()
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
