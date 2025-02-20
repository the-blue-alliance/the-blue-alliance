import json
from unittest.mock import patch

import pytest
from google.appengine.ext import ndb

from backend.common.models.district import District
from backend.common.sitevars.website_blacklist import WebsiteBlacklist
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_team_details_parser import (
    FMSAPITeamDetailsParser,
)


def test_parse_team_with_district(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2015_frc1124.json")
    with open(path, "r") as f:
        data = json.load(f)

    team_details, more_results = FMSAPITeamDetailsParser(2015).parse(data)

    assert team_details is not None
    assert len(team_details) == 1
    assert more_results is False

    team, districtTeam, robot = team_details[0]

    # Ensure we get the proper Team model back
    assert team.key_name == "frc1124"
    assert team.team_number == 1124
    assert team.name == "Avon Public Schools/UTC & AVON HIGH SCHOOL"
    assert team.nickname == "UberBots"
    assert team.city == "Avon"
    assert team.state_prov == "Connecticut"
    assert team.country == "USA"
    assert team.rookie_year == 2003
    assert team.website == "http://uberbots.org"

    # Test the DistrictTeam model we get back
    assert districtTeam is not None
    assert districtTeam.key_name == "2015ne_frc1124"
    assert districtTeam.team.string_id() == "frc1124"
    assert districtTeam.district_key, ndb.Key(District == "2015ne")

    # Test the Robot model we get back
    assert robot is not None
    assert robot.key_name == "frc1124_2015"
    assert robot.team.string_id() == "frc1124"
    assert robot.robot_name == "Orion"


def test_parse_team_with_no_district(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2015_frc254.json")
    with open(path, "r") as f:
        data = json.load(f)

    team_details, more_results = FMSAPITeamDetailsParser(2015).parse(data)

    assert team_details is not None
    assert len(team_details) == 1
    assert more_results is False

    team, districtTeam, robot = team_details[0]

    # Ensure we get the proper Team model back
    assert team.key_name == "frc254"
    assert team.team_number == 254
    assert team.name == "NASA Ames Research Center / Google"
    assert team.nickname == "The Cheesy Poofs"
    assert team.city == "San Jose"
    assert team.state_prov == "California"
    assert team.country == "USA"
    assert team.rookie_year == 1999
    assert team.website == "http://team254.com/"

    # Test the DistrictTeam model we get back
    assert districtTeam is None

    # Test the Robot model we get back
    assert robot is not None
    assert robot.key_name == "frc254_2015"
    assert robot.team.string_id() == "frc254"
    assert robot.robot_name == "Deadlift"


def test_parse_team_with_no_robot(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2015_frc2337.json")
    with open(path, "r") as f:
        data = json.load(f)

    team_details, more_results = FMSAPITeamDetailsParser(2015).parse(data)

    assert team_details is not None
    assert len(team_details) == 1
    assert more_results is False

    team, districtTeam, robot = team_details[0]

    # Ensure we get the proper Team model back
    assert team.key_name == "frc2337"
    assert team.team_number == 2337
    assert team.name == "General Motors / Premier Tooling Systems"
    assert team.nickname == "EngiNERDs"
    assert team.city == "Grand Blanc"
    assert team.state_prov == "Michigan"
    assert team.country == "USA"
    assert team.rookie_year == 2008
    assert team.website is None

    # Test the DistrictTeam model we get back
    assert districtTeam is not None
    assert districtTeam.key_name == "2015fim_frc2337"
    assert districtTeam.team.string_id() == "frc2337"
    assert districtTeam.district_key, ndb.Key(District == "2015fim")

    # Test the Robot model we get back
    assert robot is None


def test_parse_team_with_no_district_no_robot(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2015_frc2337_stub.json")
    with open(path, "r") as f:
        data = json.load(f)

    team_details, more_results = FMSAPITeamDetailsParser(2015).parse(data)

    assert team_details is not None
    assert len(team_details) == 1
    assert more_results is False

    team, districtTeam, robot = team_details[0]

    # Ensure we get the proper Team model back
    assert team.key_name == "frc2337"
    assert team.team_number == 2337
    assert team.name == "General Motors / Premier Tooling Systems"
    assert team.nickname == "EngiNERDs"
    assert team.city == "Grand Blanc"
    assert team.state_prov == "Michigan"
    assert team.country == "USA"
    assert team.rookie_year == 2008
    assert team.website is None

    # Test the DistrictTeam model we get back
    assert districtTeam is None

    # Test the Robot model we get back
    assert robot is None


@pytest.mark.parametrize(
    "website, expected_website",
    zip(
        [
            None,
            "",
            "www.firstinspires.org",
            "website.com",
            "www.website.com",
            "http://website.com",
            "https://website.com",
            "ftp://website.com",
            "http://blacklist.com/",
        ],
        [
            None,
            None,
            None,
            "http://website.com",
            "http://www.website.com",
            "http://website.com",
            "https://website.com",
            None,
            "",
        ],
    ),
)
def test_parse_team_websites(website, expected_website, test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2015_frc1124.json")
    with open(path, "r") as f:
        data = json.load(f)
        data["teams"][0]["website"] = website

    def blacklist_side_effect(website):
        if website == "http://blacklist.com/":
            return True
        return False

    with patch.object(
        WebsiteBlacklist, "is_blacklisted", side_effect=blacklist_side_effect
    ):
        team_details, more_results = FMSAPITeamDetailsParser(2015).parse(data)

    assert team_details is not None
    assert len(team_details) == 1
    assert more_results is False

    team, districtTeam, robot = team_details[0]

    assert team.key_name == "frc1124"
    assert team.website == expected_website


def test_parse_2018_teams(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2018_teams.json")
    with open(path, "r") as f:
        data = json.load(f)

    team_details, more_results = FMSAPITeamDetailsParser(2018).parse(data)

    assert team_details is not None
    assert len(team_details) == 65
    assert more_results is True


def test_parse_2018_teams_none(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2018_teams_none.json")
    with open(path, "r") as f:
        data = json.load(f)

    team_details, more_results = FMSAPITeamDetailsParser(2018).parse(data)

    assert team_details is None
    assert more_results is False


def test_parse_2017_team(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2017_frc604.json")
    with open(path, "r") as f:
        data = json.load(f)

    team_details, more_results = FMSAPITeamDetailsParser(2017).parse(data)

    assert team_details is not None
    assert len(team_details) == 1
    assert more_results is False

    team, districtTeam, robot = team_details[0]

    # Ensure we get the proper Team model back
    assert team.key_name == "frc604"
    assert team.team_number == 604
    assert (
        team.name
        == "IBM/Team Grandma/The Brin Wojcicki Foundation/BAE Systems/Boston Scientific - The Argosy Foundation/Qualcomm/Intuitive Surgical/Leland Bridge/Councilman J. Khamis/Almaden Valley Women's Club/NVIDIA/Hurricane Electric/Exatron/MDR Precision/SOLIDWORKS/Hurricane Electric/Dropbox/GitHub&Leland High"
    )
    assert team.nickname == "Quixilver"
    assert team.city == "San Jose"
    assert team.state_prov == "California"
    assert team.country == "USA"
    assert team.rookie_year == 2001
    assert team.website == "http://604Robotics.com"

    # Test the DistrictTeam model we get back
    assert districtTeam is None

    # Test the Robot model we get back
    assert robot is not None
    assert robot.key_name == "frc604_2017"
    assert robot.team.string_id() == "frc604"
    assert robot.robot_name == "Ratchet"

    # New properties for 2017
    assert team.school_name == "Leland High"
    assert team.home_cmp == "cmptx"


def test_parse_2024_offseason_demo_team(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2024_offseason_demo_team.json")
    with open(path, "r") as f:
        data = json.load(f)

    team_details, more_results = FMSAPITeamDetailsParser(2024).parse(data)

    assert team_details is not None
    assert len(team_details) == 1
    assert more_results is False

    team, districtTeam, robot = team_details[0]

    assert team.key_name == "frc9970"
    assert team.team_number == 9970
    assert team.name is None
    assert districtTeam is None
    assert robot is None
