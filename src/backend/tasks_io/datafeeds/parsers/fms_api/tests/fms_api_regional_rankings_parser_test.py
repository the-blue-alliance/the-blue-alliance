import json
from typing import Any, cast, Dict, List

from backend.common.frc_api.types import RegionalRankingTeamDetailListModelV31
from backend.common.models.regional_pool_advancement import ChampionshipStatus
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_regional_rankings_parser import (
    FMSAPIRegionalRankingsParser,
)


def test_parse_regional_rankings(test_data_importer):
    """Test parsing regional rankings with various championship statuses"""
    path = test_data_importer._get_path(__file__, "data/2025_ra_rankings.json")
    with open(path, "r") as f:
        data = json.load(f)

    parsed_data, more_results = FMSAPIRegionalRankingsParser().parse(data)
    advancement = parsed_data.advancement
    adjustments = parsed_data.adjustments

    # Should parse multiple teams with various qualification statuses
    assert len(advancement) > 0
    assert more_results is True  # Page 1 of 31, so there are more pages
    assert isinstance(adjustments, dict)

    # Check team 254 (QualifiedAtEventByAward)
    assert "frc254" in advancement
    team_254 = advancement["frc254"]
    assert team_254["cmp"] is True
    assert team_254["cmp_status"] == ChampionshipStatus.EVENT_QUALIFIED
    assert "qualifying_event" in team_254
    assert "qualifying_award_name" in team_254

    # Check team 9408 (QualifiedFromRegionalPool)
    assert "frc9408" in advancement
    team_9408 = advancement["frc9408"]
    assert team_9408["cmp"] is True
    assert team_9408["cmp_status"] == ChampionshipStatus.POOL_QUALIFIED
    assert "qualifying_pool_week" in team_9408

    # Check team 10541 (Declined - should have cmp=False)
    assert "frc10541" in advancement
    team_10541 = advancement["frc10541"]
    assert team_10541["cmp"] is False
    assert team_10541["cmp_status"] == ChampionshipStatus.EVENT_QUALIFIED


def test_parse_regional_rankings_pagination():
    """Test pagination handling"""
    data = {
        "season": 2025,
        "teams": None,
        "teamCountTotal": 1958,
        "teamCountPage": 65,
        "pageCurrent": 1,
        "pageTotal": 31,
    }

    _, more_results = FMSAPIRegionalRankingsParser().parse(data)
    assert more_results is True

    data["pageCurrent"] = 31
    _, more_results = FMSAPIRegionalRankingsParser().parse(data)
    assert more_results is False


def test_parse_regional_rankings_empty():
    """Test parsing empty response"""
    data = {
        "season": 2025,
        "teams": None,
        "teamCountTotal": 0,
        "teamCountPage": 0,
        "pageCurrent": 1,
        "pageTotal": 1,
    }

    parsed_data, more_results = FMSAPIRegionalRankingsParser().parse(data)
    advancement = parsed_data.advancement
    adjustments = parsed_data.adjustments

    assert advancement == {}
    assert adjustments == {}
    assert more_results is False


def _team(team_number: int, **fields: Any) -> Dict[str, Any]:
    team: Dict[str, Any] = {
        "rank": 1,
        "teamNumber": team_number,
        "nameShort": f"Team {team_number}",
        "totalPoints": 0,
        "championshipStatus": None,
        "qualifiedFirstCmp": False,
        "qualifiedFirstCmpDate": None,
        "qualifiedFirstCmpEventWeek": None,
        "qualifiedFirstCmpEventCode": None,
        "qualifiedFirstCmpAwardId": None,
        "qualifiedFirstCmpAwardName": None,
        "declinedFirstCmp": False,
        "declinedFirstCmpDate": None,
        "adjustPoints": 0,
    }
    team.update(fields)
    return team


def _response(teams: List[Dict[str, Any]]) -> RegionalRankingTeamDetailListModelV31:
    return cast(
        RegionalRankingTeamDetailListModelV31,
        {
            "season": 2025,
            "teams": teams,
            "teamCountTotal": len(teams),
            "teamCountPage": len(teams),
            "pageCurrent": 1,
            "pageTotal": 1,
        },
    )


def test_parse_regional_rankings_adjust_points() -> None:
    parsed_data, _ = FMSAPIRegionalRankingsParser().parse(
        _response(
            [
                _team(254, adjustPoints=5, championshipStatus="Prequalified"),
                _team(1114, adjustPoints=-3, championshipStatus="None"),
                _team(2056, adjustPoints=0, championshipStatus="Prequalified"),
            ]
        )
    )

    # Adjustments are recorded regardless of championship status; zero is skipped
    assert parsed_data.adjustments == {"frc254": 5, "frc1114": -3}
    assert set(parsed_data.advancement.keys()) == {"frc254", "frc2056"}
    assert (
        parsed_data.advancement["frc254"]["cmp_status"]
        == ChampionshipStatus.PRE_QUALIFIED
    )


def test_parse_regional_rankings_not_qualified_statuses_skipped() -> None:
    parsed_data, _ = FMSAPIRegionalRankingsParser().parse(
        _response(
            [
                _team(1, championshipStatus=None),
                _team(2, championshipStatus="None"),
                _team(3, championshipStatus="NotQualified"),
                _team(4, championshipStatus="QualifiedAtEventByRanking"),
            ]
        )
    )

    assert set(parsed_data.advancement.keys()) == {"frc4"}
    assert (
        parsed_data.advancement["frc4"]["cmp_status"]
        == ChampionshipStatus.EVENT_QUALIFIED
    )


def test_parse_regional_rankings_unknown_status_skipped() -> None:
    parsed_data, _ = FMSAPIRegionalRankingsParser().parse(
        _response(
            [
                _team(1, championshipStatus="SomeFutureStatus"),
                _team(2, championshipStatus="Prequalified"),
            ]
        )
    )

    assert set(parsed_data.advancement.keys()) == {"frc2"}
