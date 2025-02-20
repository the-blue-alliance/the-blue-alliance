import datetime
import json
import os
from typing import Set

import pytest
from freezegun import freeze_time
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.event_type import EventType
from backend.common.helpers.event_team_updater import EventTeamUpdater
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import TeamNumber
from backend.common.models.match import Match
from backend.common.models.team import Team


@pytest.fixture
def expected_teams() -> Set[TeamNumber]:
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, "data/2012ct_teams.json")

    with open(path, "r") as f:
        data = json.load(f)
        return {t["team_number"] for t in data}


@pytest.fixture
def import_event(test_data_importer) -> None:
    test_data_importer.import_event(__file__, "data/2012ct.json")


@pytest.fixture
def import_matches(test_data_importer) -> None:
    test_data_importer.import_match_list(__file__, "data/2012ct_matches.json")


@pytest.fixture
def import_awards(test_data_importer) -> None:
    test_data_importer.import_award_list(__file__, "data/2012ct_awards.json")


@pytest.fixture
def import_alliances(test_data_importer) -> None:
    test_data_importer.import_event_alliances(
        __file__, "data/2012ct_alliances.json", "2012ct"
    )


@pytest.fixture
def make_parent_event(ndb_stub) -> None:
    parent_event = Event(
        id="2012parent",
        event_short="parent",
        year=2012,
        event_type_enum=EventType.REGIONAL,
        divisions=[ndb.Key(Event, "2012ct")],
        start_date=datetime.datetime(2012, 3, 29),
        end_date=datetime.datetime(2012, 3, 31),
    )
    parent_event.put()


@freeze_time("2010-01-01")
def test_update_from_matches_future_event(
    import_event, import_matches, expected_teams
) -> None:
    teams, event_teams, et_keys_to_delete = EventTeamUpdater.update("2012ct")
    assert {team.team_number for team in teams} == expected_teams
    assert {et.key_name for et in none_throws(event_teams)} == {
        f"2012ct_frc{n}" for n in expected_teams
    }
    assert et_keys_to_delete == set()


@freeze_time("2010-01-01")
def test_does_not_delete_from_matches_future_event(
    import_event, import_matches, expected_teams
) -> None:
    event_team = EventTeam(
        id="%s_%s" % ("2012ct", "frc9999"),
        event=ndb.Key(Event, "2012ct"),
        team=ndb.Key(Team, "frc9999"),
        year=2012,
    )
    event_team.put()

    teams, event_teams, et_keys_to_delete = EventTeamUpdater.update("2012ct")
    assert {team.team_number for team in teams} == expected_teams
    assert {et.key_name for et in none_throws(event_teams)} == {
        f"2012ct_frc{n}" for n in expected_teams
    }
    assert {et_key.id() for et_key in et_keys_to_delete} == set()


@freeze_time("2012-03-30")
def test_allow_delete_from_matches_current_event(
    import_event, import_matches, expected_teams
) -> None:
    event_team = EventTeam(
        id="%s_%s" % ("2012ct", "frc9999"),
        event=ndb.Key(Event, "2012ct"),
        team=ndb.Key(Team, "frc9999"),
        year=2012,
    )
    event_team.put()

    teams, event_teams, et_keys_to_delete = EventTeamUpdater.update(
        "2012ct", allow_deletes=True
    )
    assert {team.team_number for team in teams} == expected_teams
    assert {et.key_name for et in none_throws(event_teams)} == {
        f"2012ct_frc{n}" for n in expected_teams
    }
    assert {et_key.id() for et_key in et_keys_to_delete} == {"2012ct_frc9999"}


@freeze_time("2012-06-01")
def test_update_from_matches_past_event_current_season(
    import_event, import_matches, expected_teams
) -> None:
    teams, event_teams, et_keys_to_delete = EventTeamUpdater.update("2012ct")
    assert {team.team_number for team in teams} == expected_teams
    assert {et.key_name for et in none_throws(event_teams)} == {
        f"2012ct_frc{n}" for n in expected_teams
    }

    assert et_keys_to_delete == set()


@freeze_time("2012-06-01")
def test_delete_from_matches_past_event_current_season(
    import_event, import_matches, expected_teams
) -> None:
    event_team = EventTeam(
        id="%s_%s" % ("2012ct", "frc9999"),
        event=ndb.Key(Event, "2012ct"),
        team=ndb.Key(Team, "frc9999"),
        year=2012,
    )
    event_team.put()

    teams, event_teams, et_keys_to_delete = EventTeamUpdater.update("2012ct")
    assert {team.team_number for team in teams} == expected_teams
    assert {et.key_name for et in none_throws(event_teams)} == {
        f"2012ct_frc{n}" for n in expected_teams
    }
    assert {et_key.string_id() for et_key in et_keys_to_delete} == {"2012ct_frc9999"}


@freeze_time("2015-01-01")
def test_update_from_matches_past_season(
    import_event, import_matches, expected_teams
) -> None:
    teams, event_teams, et_keys_to_delete = EventTeamUpdater.update("2012ct")
    assert {team.team_number for team in teams} == expected_teams
    assert {et.key_name for et in none_throws(event_teams)} == {
        f"2012ct_frc{n}" for n in expected_teams
    }
    assert et_keys_to_delete == set()


@freeze_time("2015-01-01")
def test_does_not_delete_from_matches_past_season(
    import_event, import_matches, expected_teams
) -> None:
    event_team = EventTeam(
        id="%s_%s" % ("2012ct", "frc9999"),
        event=ndb.Key(Event, "2012ct"),
        team=ndb.Key(Team, "frc9999"),
        year=2012,
    )
    event_team.put()

    teams, event_teams, et_keys_to_delete = EventTeamUpdater.update("2012ct")
    assert {team.team_number for team in teams} == expected_teams
    assert {et.key_name for et in none_throws(event_teams)} == {
        f"2012ct_frc{n}" for n in expected_teams
    }
    assert et_keys_to_delete == set()


@freeze_time("2012-06-01")
def test_update_from_awards(import_event, import_awards, expected_teams) -> None:
    teams, event_teams, et_keys_to_delete = EventTeamUpdater.update("2012ct")

    assert len(teams) == 22
    assert len(event_teams) == 22
    assert et_keys_to_delete == set()


@freeze_time("2012-06-01")
def test_update_from_alliances(import_event, import_alliances, expected_teams) -> None:
    teams, event_teams, et_keys_to_delete = EventTeamUpdater.update("2012ct")

    assert len(teams) == 24
    assert len(event_teams) == 24
    assert et_keys_to_delete == set()


@freeze_time("2012-06-01")
def test_update_from_division_winners_without_matches_skipped(
    import_event, make_parent_event
) -> None:
    teams, event_teams, et_keys_to_delete = EventTeamUpdater.update("2012parent")
    assert len(teams) == 0
    assert len(event_teams) == 0
    assert et_keys_to_delete == set()


@freeze_time("2012-06-01")
def test_update_from_division_winners_without_alliances_blue_wins(
    import_event, make_parent_event, import_matches
) -> None:
    teams, event_teams, et_keys_to_delete = EventTeamUpdater.update("2012parent")
    assert {team.team_number for team in teams} == {195, 20, 181}
    assert {et.key_name for et in event_teams} == {
        f"2012parent_{t.key_name}" for t in teams
    }
    assert et_keys_to_delete == set()


@freeze_time("2012-06-01")
def test_update_from_division_winners_without_alliances_red_wins(
    import_event, make_parent_event, import_matches
) -> None:
    # changes finals 3 such that red wins
    m = none_throws(Match.get_by_id("2012ct_f1m3"))

    new_alliances = m.alliances
    new_alliances[AllianceColor.BLUE]["score"] = 0
    m.alliances = new_alliances
    m.put()

    teams, event_teams, et_keys_to_delete = EventTeamUpdater.update("2012parent")
    assert {team.team_number for team in teams} == {558, 1071, 2067}
    assert {et.key_name for et in event_teams} == {
        f"2012parent_{t.key_name}" for t in teams
    }
    assert et_keys_to_delete == set()


@freeze_time("2012-06-01")
def test_update_from_division_winners_includes_backups(
    import_event, make_parent_event, import_matches, import_alliances
) -> None:
    # Change alliances #3 (the winners) to include a backup team
    event_details = none_throws(EventDetails.get_by_id("2012ct"))
    alliance = event_details.alliance_selections[2]
    alliance["backup"] = {
        "in": "frc999",
        "out": "frc181",
    }

    teams, event_teams, et_keys_to_delete = EventTeamUpdater.update("2012parent")
    assert {team.team_number for team in teams} == {195, 20, 181, 999}
    assert {et.key_name for et in event_teams} == {
        f"2012parent_{t.key_name}" for t in teams
    }
    assert et_keys_to_delete == set()
