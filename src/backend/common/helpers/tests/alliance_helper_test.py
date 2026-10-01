import unittest
from types import SimpleNamespace
from typing import cast

import pytest
from pyre_extensions import none_throws

from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.helpers.alliance_helper import AllianceHelper
from backend.common.models.alliance import PlayoffAllianceStatus, PlayoffOutcome
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


def test_alliance_size_legacy_year() -> None:
    assert (
        AllianceHelper.get_known_alliance_size(EventType.REGIONAL, 2010)
        == AllianceHelper.UNKNOWN_ALLIANCE_SIZE
    )


def test_ordinal_pick_teens() -> None:
    assert AllianceHelper.get_ordinal_pick_from_number(11) == "11th Pick"
    assert AllianceHelper.get_ordinal_pick_from_number(22) == "22nd Pick"


def test_alliance_details_backup_and_missing_team() -> None:
    event = cast(
        Event,
        SimpleNamespace(
            event_type_enum=EventType.REGIONAL,
            year=2019,
            alliance_selections=[
                {
                    "picks": ["frc1", "frc2", "frc3"],
                    "backup": {"in": "frc4", "out": "frc3"},
                    "name": "Alliance 1",
                }
            ],
        ),
    )
    alliance = none_throws(event.alliance_selections)[0]
    assert AllianceHelper.get_alliance_details_and_pick_name(event, "frc4") == (
        alliance,
        "Backup",
        3,
    )
    assert AllianceHelper.get_alliance_details_and_pick_name(event, "frc5") == (
        None,
        None,
        3,
    )


def _status(status: PlayoffOutcome, level: CompLevel) -> PlayoffAllianceStatus:
    return PlayoffAllianceStatus(
        level=level,
        status=status,
        record=None,
        current_level_record={"wins": 1, "losses": 1, "ties": 0},
        playoff_type=PlayoffType.BRACKET_8_TEAM,
    )


def test_playoff_status_string_plural_playing() -> None:
    assert AllianceHelper.generate_playoff_status_string(
        _status(PlayoffOutcome.PLAYING, CompLevel.SF), None, None, plural=True
    ) == ["are <b>1-1-0</b> in the <b>Semifinals</b>"]


def test_playoff_status_string_won_level() -> None:
    assert AllianceHelper.generate_playoff_status_string(
        _status(PlayoffOutcome.WON, CompLevel.SF), None, None
    ) == ["<b>won the Semifinals</b>"]


def test_playoff_status_string_unknown_status() -> None:
    with pytest.raises(Exception, match="Unknown playoff status"):
        AllianceHelper.generate_playoff_status_string(
            _status(cast(PlayoffOutcome, "bogus"), CompLevel.SF), None, None
        )
