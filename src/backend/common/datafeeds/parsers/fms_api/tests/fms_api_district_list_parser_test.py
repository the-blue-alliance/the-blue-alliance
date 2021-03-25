import json

from google.cloud import ndb

from backend.common.datafeeds.parsers.fms_api.fms_api_district_list_parser import (
    FMSAPIDistrictListParser,
)


def test_parse_district_list(test_data_importer, ndb_client: ndb.Client) -> None:
    path = test_data_importer._get_path(__file__, "data/2018_districts.json")
    with open(path, "r") as f:
        data = json.load(f)

    with ndb_client.context():
        districts = FMSAPIDistrictListParser(2018).parse(data)

    assert districts is not None
    assert len(districts) == 10

    new_england = districts[7]
    assert new_england.key_name == "2018ne"
    assert new_england.abbreviation == "ne"
    assert new_england.year == 2018
    assert new_england.display_name == "New England"


def test_parse_district_list_none(test_data_importer, ndb_client: ndb.Client) -> None:
    path = test_data_importer._get_path(__file__, "data/2018_no_districts.json")
    with open(path, "r") as f:
        data = json.load(f)

    with ndb_client.context():
        districts = FMSAPIDistrictListParser(2018).parse(data)

    assert districts is None
