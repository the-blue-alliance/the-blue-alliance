import json

from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_event_alliances_parser import (
    FMSAPIEventAlliancesParser,
)


def test_parse_no_alliances(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2016_no_alliances.json")
    with open(path, "r") as f:
        data = json.load(f)

    alliances = FMSAPIEventAlliancesParser().parse(data)
    assert alliances is None


def test_parse_8alliances(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2016_nyny_alliances.json")
    with open(path, "r") as f:
        data = json.load(f)

    alliances = FMSAPIEventAlliancesParser().parse(data)

    assert len(alliances) == 8

    # Ensure that we have the alliances in the proper order and that backup teams propegate
    for i in range(len(alliances)):
        alliance = alliances[i]
        alliance_number = i + 1
        assert alliance["name"] == "Alliance {}".format(alliance_number)
        assert alliance.get("backup") is None


def test_parse_16alliances(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2016_micmp_alliances.json")
    with open(path, "r") as f:
        data = json.load(f)

    alliances = FMSAPIEventAlliancesParser().parse(data)

    assert len(alliances) == 16

    for i in range(len(alliances)):
        alliance = alliances[i]
        alliance_number = i + 1
        assert alliance["name"] == "Alliance {}".format(alliance_number)
        assert alliance.get("backup") is None


def test_parse_4team(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2015_curie_alliances.json")
    with open(path, "r") as f:
        data = json.load(f)

    alliances = FMSAPIEventAlliancesParser().parse(data)

    assert len(alliances) == 8

    for i in range(len(alliances)):
        alliance = alliances[i]
        alliance_number = i + 1
        assert alliance["name"] == "Alliance {}".format(alliance_number)
        assert alliance.get("backup") is None


def test_parse_backup_team_used(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2016_necmp_alliances.json")
    with open(path, "r") as f:
        data = json.load(f)

    alliances = FMSAPIEventAlliancesParser().parse(data)

    assert len(alliances) == 8

    for i in range(len(alliances)):
        alliance = alliances[i]
        alliance_number = i + 1

        assert alliance["name"] == "Alliance {}".format(alliance_number)

        if alliance_number == 5:
            assert alliance["backup"] is not None
            assert alliance["backup"]["in"] == "frc4905"
            assert alliance["backup"]["out"] == "frc999"
        else:
            assert alliance.get("backup") is None


def test_parse_ignore_no_picks(test_data_importer):
    path = test_data_importer._get_path(__file__, "data/2019_ohwa2_alliances.json")
    with open(path, "r") as f:
        data = json.load(f)

    alliances = FMSAPIEventAlliancesParser().parse(data)

    assert len(alliances) == 7
