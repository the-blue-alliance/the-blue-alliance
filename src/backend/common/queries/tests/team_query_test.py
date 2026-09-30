from google.appengine.ext import ndb

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.regional_pool_team import RegionalPoolTeam
from backend.common.models.team import Team
from backend.common.queries.team_query import (
    get_team_page_num,
    RegionalTeamsQuery,
    TeamListQuery,
    TeamQuery,
)


def test_team_not_found() -> None:
    team = TeamQuery(team_key="frc254").fetch()
    assert team is None


def test_team_is_found() -> None:
    Team(id="frc254", team_number=254).put()
    result = TeamQuery(team_key="frc254").fetch()
    assert result is not None
    assert result.team_number == 254


def test_get_team_page_num() -> None:
    assert get_team_page_num("frc1") == 0
    assert get_team_page_num(f"frc{TeamListQuery.PAGE_SIZE}") == 1
    assert get_team_page_num("frc9999") == int(9999 / TeamListQuery.PAGE_SIZE)


def test_regional_teams_query() -> None:
    RegionalPoolTeam(id="2025_frc254", team=ndb.Key(Team, "frc254"), year=2025).put()
    RegionalPoolTeam(id="2024_frc604", team=ndb.Key(Team, "frc604"), year=2024).put()

    assert RegionalTeamsQuery(year=2025).fetch() == [ndb.Key(Team, "frc254")]


def test_bug_29_regional_teams_query_fetch_dict() -> None:
    """
    Bug #29: RegionalTeamsQuery returns team Keys, but its DICT_CONVERTER is
    TeamConverter, which expects Team models, so fetch_dict always raises
    AttributeError.

    Correct: fetch_dict returns the declared dict type, List[str] of team
    keys.
    """
    RegionalPoolTeam(id="2025_frc254", team=ndb.Key(Team, "frc254"), year=2025).put()

    assert RegionalTeamsQuery(year=2025).fetch_dict(ApiMajorVersion.API_V3) == [
        "frc254"
    ]
