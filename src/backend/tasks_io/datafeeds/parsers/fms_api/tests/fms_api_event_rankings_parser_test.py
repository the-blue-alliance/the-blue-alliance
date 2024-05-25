import json

from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_event_rankings_parser import (
    FMSAPIEventRankingsParser,
)


def test_parse_event_rankings_none(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2015miket_rankings_none.json")
    with open(path, "r") as f:
        data = json.load(f)

    rankings = FMSAPIEventRankingsParser(2015).parse(data)

    assert rankings is None


def test_parse_event_rankings_2015(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2015miket_rankings.json")
    with open(path, "r") as f:
        data = json.load(f)

    rankings = FMSAPIEventRankingsParser(2015).parse(data)

    assert rankings is not None
    assert len(rankings) == 41

    # Spot check rankings
    one = rankings[0]
    assert one is not None
    assert one == {
        "dq": 0,
        "matches_played": 12,
        "qual_average": 76.83,
        "rank": 1,
        "record": None,
        "sort_orders": [76.83, 160.0, 12.0, 348.0, 262.0, 140.0],
        "team_key": "frc314",
    }

    ten = rankings[9]
    assert ten is not None
    assert ten == {
        "dq": 0,
        "matches_played": 12,
        "qual_average": 42.5,
        "rank": 10,
        "record": None,
        "sort_orders": [42.5, 40.0, 56.0, 116.0, 146.0, 158.0],
        "team_key": "frc5282",
    }


def test_parse_event_rankings_2016(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2016miket_rankings.json")
    with open(path, "r") as f:
        data = json.load(f)

    rankings = FMSAPIEventRankingsParser(2016).parse(data)

    assert rankings is not None
    assert len(rankings) == 40

    # Spot check rankings
    one = rankings[0]
    assert one is not None
    assert one == {
        "dq": 0,
        "matches_played": 12,
        "qual_average": None,
        "rank": 1,
        "record": {"losses": 2, "ties": 0, "wins": 10},
        "sort_orders": [33.0, 166.0, 130.0, 99.0, 625.0, 0.48],
        "team_key": "frc5150",
    }

    ten = rankings[9]
    assert ten is not None
    assert ten == {
        "dq": 0,
        "matches_played": 12,
        "qual_average": None,
        "rank": 10,
        "record": {"losses": 5, "ties": 0, "wins": 7},
        "sort_orders": [23.0, 236.0, 125.0, 113.0, 595.0, 0.13],
        "team_key": "frc3535",
    }


def test_parse_event_rankings_2017(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2017miket_rankings.json")
    with open(path, "r") as f:
        data = json.load(f)

    rankings = FMSAPIEventRankingsParser(2017).parse(data)

    assert rankings is not None
    assert len(rankings) == 38

    # Spot check rankings
    one = rankings[0]
    assert one is not None
    assert one == {
        "dq": 0,
        "matches_played": 12,
        "qual_average": None,
        "rank": 1,
        "record": {"losses": 2, "ties": 0, "wins": 10},
        "sort_orders": [1.66, 2661.0, 629.0, 1320.0, 950.0, 6.0],
        "team_key": "frc2619",
    }

    ten = rankings[9]
    assert ten is not None
    assert ten == {
        "dq": 0,
        "matches_played": 12,
        "qual_average": None,
        "rank": 10,
        "record": {"losses": 5, "ties": 0, "wins": 7},
        "sort_orders": [1.16, 2695.0, 395.0, 1400.0, 1050.0, 5.0],
        "team_key": "frc5150",
    }


def test_parse_event_rankings_2020(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2020miket_rankings.json")
    with open(path, "r") as f:
        data = json.load(f)

    rankings = FMSAPIEventRankingsParser(2020).parse(data)

    assert rankings is not None
    assert len(rankings) == 40

    # Spot check rankings
    one = rankings[0]
    assert one is not None
    assert one == {
        "dq": 0,
        "matches_played": 12,
        "qual_average": None,
        "rank": 1,
        "record": {"losses": 0, "ties": 0, "wins": 12},
        "sort_orders": [2.5, 485.0, 620.0, 350.0, 0.0, 0.0],
        "team_key": "frc2337",
    }

    ten = rankings[9]
    assert ten is not None
    assert ten == {
        "dq": 0,
        "matches_played": 12,
        "qual_average": None,
        "rank": 10,
        "record": {"losses": 3, "ties": 1, "wins": 8},
        "sort_orders": [1.5, 361.0, 255.0, 239.0, 0.0, 0.0],
        "team_key": "frc5641",
    }
