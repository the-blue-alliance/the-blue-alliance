import unittest

import pytest
from google.cloud import ndb

from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.event_team_status import (
    EventTeamStatus,
    EventTeamStatusAlliance,
)
from backend.common.models.team import Team


@pytest.mark.usefixtures("ndb_context")
class TestTeamManipulator(unittest.TestCase):
    def setUp(self):
        self.old_team = EventTeam(
            id="2010cmp_frc177",
            team=ndb.Key(Team, "frc177"),
            event=ndb.Key(Event, "2010cmp"),
            year=2010,
        )

        self.new_team = EventTeam(
            id="2010cmp_frc177",
            team=ndb.Key(Team, "frc177"),
            event=ndb.Key(Event, "2010cmp"),
            year=2010,
            status=EventTeamStatus(
                qual=None,
                playoff=None,
                alliance=EventTeamStatusAlliance(
                    name=None,
                    number=1,
                    pick=1,
                    backup=None,
                ),
            ),
        )

    def assertOldEventTeam(self, event_team: EventTeam) -> None:
        assert event_team.team.id() == "frc177"
        assert event_team.event.id() == "2010cmp"
        assert event_team.year == 2010

    def assertMergedEventTeam(self, event_team: EventTeam) -> None:
        self.assertOldEventTeam(event_team)
        assert event_team.status is not None
        assert event_team.status["alliance"]["number"] == 1

    def test_createOrUpdate(self):
        EventTeamManipulator.createOrUpdate(self.old_team)
        self.assertOldEventTeam(EventTeam.get_by_id("2010cmp_frc177"))
        EventTeamManipulator.createOrUpdate(self.new_team)
        self.assertMergedEventTeam(EventTeam.get_by_id("2010cmp_frc177"))

    def test_findOrSpawn(self):
        self.old_team.put()
        self.assertMergedEventTeam(EventTeamManipulator.findOrSpawn(self.new_team))

    def test_updateMerge(self):
        self.assertMergedEventTeam(
            EventTeamManipulator.updateMerge(self.new_team, self.old_team)
        )
