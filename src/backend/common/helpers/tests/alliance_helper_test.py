import unittest

import pytest
from pyre_extensions import none_throws

from backend.common.helpers.alliance_helper import AllianceHelper
from backend.common.models.event import Event
from backend.tests.json_data_importer import JsonDataImporter  # noqa


@pytest.mark.usefixtures("ndb_context")
class Test2023njflaAllianceHelper(unittest.TestCase):
    alliance_one = {
        "declines": [],
        "name": "Alliance 1",
        "picks": ["frc11", "frc1676", "frc4573"],
        "status": {
            "current_level_record": {"losses": 2, "ties": 0, "wins": 0},
            "level": "f",
            "playoff_average": None,
            "record": {"losses": 3, "ties": 0, "wins": 3},
            "status": "eliminated",
        },
    }

    alliance_four = {
        "declines": [],
        "name": "Alliance 4",
        "picks": ["frc3142", "frc1279", "frc1672", "frc5732"],
        "status": {
            "current_level_record": {"losses": 2, "ties": 0, "wins": 3},
            "level": "sf",
            "playoff_average": None,
            "record": {"losses": 2, "ties": 0, "wins": 3},
            "status": "eliminated",
        },
    }

    def setUp(self) -> None:
        test_data_importer = JsonDataImporter()
        test_data_importer.import_event(__file__, "data/2023njfla.json")
        test_data_importer.import_event_alliances(
            __file__, "data/2023njfla_alliances.json", "2023njfla"
        )

        self.event: Event = none_throws(Event.get_by_id("2023njfla"))

    def test_alliance_size(self):
        self.assertEqual(
            AllianceHelper.get_known_alliance_size(
                self.event.event_type_enum, self.event.year
            ),
            3,
        )

    def test_alliance_and_pick_names(self):
        self.assertEqual(
            AllianceHelper.get_alliance_details_and_pick_name(self.event, "frc11"),
            (self.alliance_one, "Captain", 3),
        )
        self.assertEqual(
            AllianceHelper.get_alliance_details_and_pick_name(self.event, "frc1676"),
            (self.alliance_one, "1st Pick", 3),
        )
        self.assertEqual(
            AllianceHelper.get_alliance_details_and_pick_name(self.event, "frc4573"),
            (self.alliance_one, "2nd Pick", 3),
        )

        self.assertEqual(
            AllianceHelper.get_alliance_details_and_pick_name(self.event, "frc3142"),
            (self.alliance_four, "Captain", 3),
        )
        self.assertEqual(
            AllianceHelper.get_alliance_details_and_pick_name(self.event, "frc1279"),
            (self.alliance_four, "1st Pick", 3),
        )
        self.assertEqual(
            AllianceHelper.get_alliance_details_and_pick_name(self.event, "frc1672"),
            (self.alliance_four, "2nd Pick", 3),
        )
        self.assertEqual(
            AllianceHelper.get_alliance_details_and_pick_name(self.event, "frc5732"),
            (self.alliance_four, "Backup", 3),
        )

    def test_alliance_status_string(self):
        self.assertEqual(
            AllianceHelper.generate_playoff_status_string(
                self.alliance_one["status"],
                "Captain",
                "Alliance 1",
                plural=True,
                include_record=False,
            ),
            [
                "competed in the playoffs as the <b>Captain</b> of <b>Alliance 1</b>",
                "were eliminated in the <b>Finals</b>",
            ],
        )
        self.assertEqual(
            AllianceHelper.generate_playoff_status_string(
                self.alliance_four["status"],
                "1st Pick",
                "Alliance 4",
                plural=True,
                include_record=False,
            ),
            [
                "competed in the playoffs as the <b>1st Pick</b> of <b>Alliance 4</b>",
                "were eliminated in the <b>Semifinals</b>",
            ],
        )
