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
