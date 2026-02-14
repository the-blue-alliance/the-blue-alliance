from backend.common.models.regional_pool_advancement import ChampionshipStatus
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_regional_rankings_parser import (
    FMSAPIRegionalRankingsParser,
)


def test_parse_regional_rankings(test_data_importer):
    """Test parsing regional rankings with various championship statuses"""
    data = {
        "season": 2025,
        "teams": [
            {
                "rank": 1,
                "teamNumber": 254,
                "nameShort": "The Cheesy Poofs",
                "regional1Points": 100,
                "regional1Details": {
                    "tournamentCode": "CAFR",
                    "totalPoints": 100,
                    "qualificationPerformancePoints": 50,
                    "allianceSelectionPoints": 20,
                    "playoffAdvancementPoints": 20,
                    "awardPoints": 10,
                    "teamAgePoints": 0,
                    "awardId": 1,
                },
                "regional2PointsProjection": None,
                "regional2Points": 90,
                "regional2Details": {
                    "tournamentCode": "CASJ",
                    "totalPoints": 90,
                    "qualificationPerformancePoints": 45,
                    "allianceSelectionPoints": 20,
                    "playoffAdvancementPoints": 15,
                    "awardPoints": 10,
                    "teamAgePoints": 0,
                    "awardId": 1,
                },
                "regionalDirectPoints": None,
                "regionalDirectDetails": {
                    "tournamentCode": None,
                    "totalPoints": 0,
                    "qualificationPerformancePoints": 0,
                    "allianceSelectionPoints": 0,
                    "playoffAdvancementPoints": 0,
                    "awardPoints": 0,
                    "teamAgePoints": 0,
                    "awardId": 0,
                },
                "totalPoints": 190,
                "championshipStatus": "QualifiedFromRegionalPool",
                "qualifiedFirstCmp": True,
                "qualifiedFirstCmpDate": "2025-03-15",
                "qualifiedFirstCmpEventWeek": 3,
                "qualifiedFirstCmpEventCode": "CAFR",
                "qualifiedFirstCmpAwardId": 1,
                "qualifiedFirstCmpAwardName": "Winner",
                "declinedFirstCmp": False,
                "declinedFirstCmpDate": None,
                "tiebreakers": None,
                "adjustPoints": 0,
            },
            {
                "rank": 2,
                "teamNumber": 1678,
                "nameShort": "Citrus Circuits",
                "regional1Points": 95,
                "regional1Details": {
                    "tournamentCode": "CADA",
                    "totalPoints": 95,
                    "qualificationPerformancePoints": 48,
                    "allianceSelectionPoints": 20,
                    "playoffAdvancementPoints": 17,
                    "awardPoints": 10,
                    "teamAgePoints": 0,
                    "awardId": 1,
                },
                "regional2PointsProjection": None,
                "regional2Points": None,
                "regional2Details": {
                    "tournamentCode": None,
                    "totalPoints": 0,
                    "qualificationPerformancePoints": 0,
                    "allianceSelectionPoints": 0,
                    "playoffAdvancementPoints": 0,
                    "awardPoints": 0,
                    "teamAgePoints": 0,
                    "awardId": 0,
                },
                "regionalDirectPoints": None,
                "regionalDirectDetails": {
                    "tournamentCode": None,
                    "totalPoints": 0,
                    "qualificationPerformancePoints": 0,
                    "allianceSelectionPoints": 0,
                    "playoffAdvancementPoints": 0,
                    "awardPoints": 0,
                    "teamAgePoints": 0,
                    "awardId": 0,
                },
                "totalPoints": 95,
                "championshipStatus": "QualifiedAtEventByAward",
                "qualifiedFirstCmp": True,
                "qualifiedFirstCmpDate": "2025-03-10",
                "qualifiedFirstCmpEventWeek": 2,
                "qualifiedFirstCmpEventCode": "CADA",
                "qualifiedFirstCmpAwardId": 69,
                "qualifiedFirstCmpAwardName": "Chairman's Award",
                "declinedFirstCmp": False,
                "declinedFirstCmpDate": None,
                "tiebreakers": None,
                "adjustPoints": 5,
            },
            {
                "rank": 100,
                "teamNumber": 9999,
                "nameShort": "Not Qualified",
                "regional1Points": 10,
                "regional1Details": {
                    "tournamentCode": "CASJ",
                    "totalPoints": 10,
                    "qualificationPerformancePoints": 8,
                    "allianceSelectionPoints": 2,
                    "playoffAdvancementPoints": 0,
                    "awardPoints": 0,
                    "teamAgePoints": 0,
                    "awardId": 0,
                },
                "regional2PointsProjection": None,
                "regional2Points": None,
                "regional2Details": {
                    "tournamentCode": None,
                    "totalPoints": 0,
                    "qualificationPerformancePoints": 0,
                    "allianceSelectionPoints": 0,
                    "playoffAdvancementPoints": 0,
                    "awardPoints": 0,
                    "teamAgePoints": 0,
                    "awardId": 0,
                },
                "regionalDirectPoints": None,
                "regionalDirectDetails": {
                    "tournamentCode": None,
                    "totalPoints": 0,
                    "qualificationPerformancePoints": 0,
                    "allianceSelectionPoints": 0,
                    "playoffAdvancementPoints": 0,
                    "awardPoints": 0,
                    "teamAgePoints": 0,
                    "awardId": 0,
                },
                "totalPoints": 10,
                "championshipStatus": "NotQualified",
                "qualifiedFirstCmp": False,
                "qualifiedFirstCmpDate": None,
                "qualifiedFirstCmpEventWeek": 0,
                "qualifiedFirstCmpEventCode": None,
                "qualifiedFirstCmpAwardId": 0,
                "qualifiedFirstCmpAwardName": None,
                "declinedFirstCmp": False,
                "declinedFirstCmpDate": None,
                "tiebreakers": None,
                "adjustPoints": 0,
            },
        ],
        "teamCountTotal": 3,
        "teamCountPage": 3,
        "pageCurrent": 1,
        "pageTotal": 1,
    }

    parsed_data, more_results = FMSAPIRegionalRankingsParser().parse(data)
    advancement = parsed_data.advancement
    adjustments = parsed_data.adjustments

    # Should parse 2 teams (254 and 1678), not 9999 (NotQualified)
    assert len(advancement) == 2
    assert more_results is False

    # Check team 254
    assert "frc254" in advancement
    team_254 = advancement["frc254"]
    assert team_254["cmp"] is True
    assert team_254["cmp_status"] == ChampionshipStatus.POOL_QUALIFIED
    assert team_254["qualifying_event"] == "2025cafr"
    assert team_254["qualifying_award_name"] == "Winner"
    assert team_254["qualifying_pool_week"] == 3

    # Check team 1678
    assert "frc1678" in advancement
    team_1678 = advancement["frc1678"]
    assert team_1678["cmp"] is True
    assert team_1678["cmp_status"] == ChampionshipStatus.EVENT_QUALIFIED
    assert team_1678["qualifying_event"] == "2025cada"
    assert team_1678["qualifying_award_name"] == "Chairman's Award"
    assert team_1678["qualifying_pool_week"] == 2

    # Check team 9999 is not present (NotQualified)
    assert "frc9999" not in advancement

    # Check adjustments
    assert adjustments == {"frc1678": 5}


def test_parse_regional_rankings_declined(test_data_importer):
    """Test parsing regional rankings with declined teams"""
    data = {
        "season": 2025,
        "teams": [
            {
                "rank": 1,
                "teamNumber": 1234,
                "nameShort": "Declined Team",
                "regional1Points": 100,
                "regional1Details": {
                    "tournamentCode": "TEST",
                    "totalPoints": 100,
                    "qualificationPerformancePoints": 50,
                    "allianceSelectionPoints": 20,
                    "playoffAdvancementPoints": 20,
                    "awardPoints": 10,
                    "teamAgePoints": 0,
                    "awardId": 1,
                },
                "regional2PointsProjection": None,
                "regional2Points": None,
                "regional2Details": {
                    "tournamentCode": None,
                    "totalPoints": 0,
                    "qualificationPerformancePoints": 0,
                    "allianceSelectionPoints": 0,
                    "playoffAdvancementPoints": 0,
                    "awardPoints": 0,
                    "teamAgePoints": 0,
                    "awardId": 0,
                },
                "regionalDirectPoints": None,
                "regionalDirectDetails": {
                    "tournamentCode": None,
                    "totalPoints": 0,
                    "qualificationPerformancePoints": 0,
                    "allianceSelectionPoints": 0,
                    "playoffAdvancementPoints": 0,
                    "awardPoints": 0,
                    "teamAgePoints": 0,
                    "awardId": 0,
                },
                "totalPoints": 100,
                "championshipStatus": "QualifiedFromRegionalPool",
                "qualifiedFirstCmp": True,
                "qualifiedFirstCmpDate": "2025-03-15",
                "qualifiedFirstCmpEventWeek": 3,
                "qualifiedFirstCmpEventCode": "TEST",
                "qualifiedFirstCmpAwardId": 1,
                "qualifiedFirstCmpAwardName": "Winner",
                "declinedFirstCmp": True,
                "declinedFirstCmpDate": "2025-03-20",
                "tiebreakers": None,
                "adjustPoints": 0,
            }
        ],
        "teamCountTotal": 1,
        "teamCountPage": 1,
        "pageCurrent": 1,
        "pageTotal": 1,
    }

    parsed_data, more_results = FMSAPIRegionalRankingsParser().parse(data)
    advancement = parsed_data.advancement

    assert len(advancement) == 1
    assert "frc1234" in advancement
    team_1234 = advancement["frc1234"]
    assert team_1234["cmp"] is False  # Declined
    assert team_1234["cmp_status"] == ChampionshipStatus.POOL_QUALIFIED


def test_parse_regional_rankings_pagination():
    """Test pagination handling"""
    data = {
        "season": 2025,
        "teams": [],
        "teamCountTotal": 200,
        "teamCountPage": 50,
        "pageCurrent": 1,
        "pageTotal": 4,
    }

    _, more_results = FMSAPIRegionalRankingsParser().parse(data)
    assert more_results is True

    data["pageCurrent"] = 4
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
