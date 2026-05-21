import json

from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_district_rankings_parser import (
    FMSAPIDistrictRankingsParser,
)


def test_parse_district_rankings(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2019fim_rankings.json")
    with open(path, "r") as f:
        data = json.load(f)

    data, more_results = FMSAPIDistrictRankingsParser().parse(data)
    rankings = data.advancement

    assert len(rankings) == 65
    assert more_results

    assert rankings["frc27"] is not None
    assert rankings["frc27"]["dcmp"]
    assert rankings["frc27"]["cmp"]

    assert rankings["frc3572"] is not None
    assert rankings["frc3572"]["dcmp"] is False
    assert rankings["frc3572"]["cmp"] is False

    assert rankings["frc5084"] is not None
    assert rankings["frc5084"]["dcmp"]
    assert rankings["frc5084"]["cmp"] is False

    assert rankings["frc2771"] is not None
    assert rankings["frc2771"]["dcmp"] is False
    assert rankings["frc2771"]["cmp"]


def test_parse_district_rankings_end(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2019fim_rankings_end.json")
    with open(path, "r") as f:
        data = json.load(f)

    data, more_results = FMSAPIDistrictRankingsParser().parse(data)
    rankings = data.advancement

    assert len(rankings) == 22
    assert more_results is False


def test_parse_district_rankings_empty(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2019fim_rankings_none.json")
    with open(path, "r") as f:
        data = json.load(f)

    data, more_results = FMSAPIDistrictRankingsParser().parse(data)
    rankings = data.advancement

    assert rankings == {}
    assert more_results is False


def test_parse_district_rankings_adjustments(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2025fit_rankings.json")
    with open(path, "r") as f:
        data = json.load(f)

    data, _ = FMSAPIDistrictRankingsParser().parse(data)
    adjustments = data.adjustments

    assert adjustments == {
        "frc10014": 1,
        "frc2158": 7,
        "frc2689": 7,
        "frc5261": 1,
        "frc6672": 7,
        "frc7691": 3,
        "frc9658": 1,
    }


def test_parse_district_rankings_api_team_data(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2025fit_rankings.json")
    with open(path, "r") as f:
        data = json.load(f)

    data, _ = FMSAPIDistrictRankingsParser().parse(data)

    assert data.api_team_data["frc118"] == {
        "rank": 1,
        "total_points": 149,
        "team_age_points": 0,
        "event1_code": "TXTOM",
        "event1_points": 73,
        "event2_code": "TXMAN",
        "event2_points": 76,
        "district_cmp_code": None,
        "district_cmp_points": 0,
    }
    assert data.api_team_data["frc3005"]["rank"] == 2
    assert data.api_team_data["frc6672"] == {
        "rank": 17,
        "total_points": 95,
        "team_age_points": 0,
        "event1_code": "TXWAC",
        "event1_points": 44,
        "event2_code": "TXFOR",
        "event2_points": 44,
        "district_cmp_code": None,
        "district_cmp_points": 0,
    }
