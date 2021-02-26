import json
import unittest

import pytest
from google.cloud import ndb

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.manipulators.award_manipulator import AwardManipulator
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.team import Team


@pytest.mark.usefixtures("ndb_context")
class TestAwardManipulator(unittest.TestCase):
    def setUp(self):
        self.event = Event(
            id="2013casj",
            event_short="casj",
            year=2013,
            event_type_enum=EventType.REGIONAL,
        )

        self.old_award = Award(
            id=Award.render_key_name(self.event.key_name, AwardType.WINNER),
            name_str="Regional Winner",
            award_type_enum=AwardType.WINNER,
            year=2013,
            event=self.event.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[ndb.Key(Team, "frc111"), ndb.Key(Team, "frc234")],
            recipient_json_list=[
                json.dumps({"team_number": 111, "awardee": None}),
                json.dumps({"team_number": 234, "awardee": None}),
            ],
        )

        self.new_award = Award(
            id="2013casj_1",
            name_str="Regional Champion",
            award_type_enum=AwardType.WINNER,
            year=2013,
            event=self.event.key,
            event_type_enum=EventType.REGIONAL,
            team_list=[ndb.Key(Team, "frc359")],
            recipient_json_list=[json.dumps({"team_number": 359, "awardee": None})],
        )

    def assertMergedAward(self, award, is_auto_union):
        self.assertEqual(award.name_str, "Regional Champion")
        self.assertEqual(award.award_type_enum, AwardType.WINNER)
        self.assertEqual(award.year, 2013)
        self.assertEqual(award.event, self.event.key)
        self.assertEqual(award.event_type_enum, EventType.REGIONAL)
        if is_auto_union:
            self.assertEqual(
                set(award.team_list),
                {
                    ndb.Key(Team, "frc111"),
                    ndb.Key(Team, "frc234"),
                    ndb.Key(Team, "frc359"),
                },
            )
            self.assertEqual(len(award.recipient_json_list), 3)
            for r in award.recipient_json_list:
                self.assertTrue(
                    json.loads(r)
                    in [
                        {"team_number": 111, "awardee": None},
                        {"team_number": 234, "awardee": None},
                        {"team_number": 359, "awardee": None},
                    ]
                )
        else:
            self.assertEqual(set(award.team_list), {ndb.Key(Team, "frc359")})
            self.assertEqual(len(award.recipient_json_list), 1)
            for r in award.recipient_json_list:
                self.assertTrue(
                    json.loads(r) in [{"team_number": 359, "awardee": None}]
                )

    def assertOldAward(self, award):
        self.assertEqual(award.name_str, "Regional Winner")
        self.assertEqual(award.award_type_enum, AwardType.WINNER)
        self.assertEqual(award.year, 2013)
        self.assertEqual(award.event, self.event.key)
        self.assertEqual(award.event_type_enum, EventType.REGIONAL)
        self.assertEqual(
            set(award.team_list), {ndb.Key(Team, "frc111"), ndb.Key(Team, "frc234")}
        )
        self.assertEqual(len(award.recipient_json_list), 2)
        for r in award.recipient_json_list:
            self.assertTrue(
                json.loads(r)
                in [
                    {"team_number": 111, "awardee": None},
                    {"team_number": 234, "awardee": None},
                ]
            )

    def test_createOrUpdateupdate(self):
        AwardManipulator.createOrUpdate(self.old_award)
        self.assertOldAward(Award.get_by_id("2013casj_1"))

        AwardManipulator.createOrUpdate(self.new_award)
        self.assertMergedAward(Award.get_by_id("2013casj_1"), True)

    def test_findOrSpawn(self):
        self.old_award.put()
        self.assertMergedAward(AwardManipulator.findOrSpawn(self.new_award), True)

    def test_updateMerge(self):
        self.assertMergedAward(
            AwardManipulator.updateMerge(self.new_award, self.old_award), True
        )

    def test_createOrUpdate_no_auto_union(self):
        AwardManipulator.createOrUpdate(self.old_award)
        self.assertOldAward(Award.get_by_id("2013casj_1"))

        AwardManipulator.createOrUpdate(self.new_award, auto_union=False)
        self.assertMergedAward(Award.get_by_id("2013casj_1"), False)

    def test_findOrSpawn_no_auto_union(self):
        self.old_award.put()
        self.assertMergedAward(
            AwardManipulator.findOrSpawn(self.new_award, auto_union=False), False
        )

    def test_updateMerge_no_auto_union(self):
        self.assertMergedAward(
            AwardManipulator.updateMerge(
                self.new_award, self.old_award, auto_union=False
            ),
            False,
        )
