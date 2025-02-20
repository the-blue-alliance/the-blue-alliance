import unittest

import pytest
from _pytest.monkeypatch import MonkeyPatch
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.playoff_type import DoubleElimRound, PlayoffType
from backend.common.helpers.event_team_status_helper import EventTeamStatusHelper
from backend.common.models.alliance import PlayoffOutcome
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_team_status import (
    EventTeamLevelStatus,
)
from backend.common.models.match import Match
from backend.common.tests.event_simulator import EventSimulator
from backend.common.tests.fixture_loader import load_fixture
from backend.tests.json_data_importer import JsonDataImporter  # noqa


@pytest.fixture(autouse=True)
def disable_db_query_cache(monkeypatch: MonkeyPatch):
    # This test doesn't fully clear all the DB caches it needs to, s
    # just disable writing cached query results for it
    from backend.common.queries.database_query import CachedDatabaseQuery

    monkeypatch.setattr(CachedDatabaseQuery, "CACHE_WRITES_ENABLED", False)


@pytest.fixture(autouse=True)
def auto_add_ndb_stub(ndb_stub) -> None:
    # prevent global state from leaking
    ndb.get_context().clear_cache()


@pytest.mark.usefixtures("ndb_stub", "taskqueue_stub")
class TestSimulated2016nytrEventTeamStatusHelper(unittest.TestCase):
    maxDiff = None

    def test_simulated_event(self):
        es = EventSimulator()
        event = Event.get_by_id("2016nytr")

        es.step()
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 is <b>Rank 15/36</b> with a record of <b>0-0-0</b> in quals.",
        )

        for _ in range(5):
            es.step()
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 is <b>Rank 6/36</b> with a record of <b>1-0-0</b> in quals.",
        )

        for _ in range(67):
            es.step()
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 was <b>Rank 1/36</b> with a record of <b>11-1-0</b> in quals.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5240", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 was <b>Rank 4/36</b> with a record of <b>9-3-0</b> in quals.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc229", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc229", status
            ),
            "Team 229 was <b>Rank 16/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc1665", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1665", status
            ),
            "Team 1665 was <b>Rank 15/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5964", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5964", status
            ),
            "Team 5964 was <b>Rank 21/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        es.step()  # Alliance selections added
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 was <b>Rank 1/36</b> with a record of <b>11-1-0</b> in quals and will be competing in the playoffs as the <b>Captain</b> of <b>Alliance 1</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5240", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 was <b>Rank 4/36</b> with a record of <b>9-3-0</b> in quals and will be competing in the playoffs as the <b>1st Pick</b> of <b>Alliance 4</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc229", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc229", status
            ),
            "Team 229 was <b>Rank 16/36</b> with a record of <b>6-6-0</b> in quals and will be competing in the playoffs as the <b>2nd Pick</b> of <b>Alliance 2</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc1665", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1665", status
            ),
            "Team 1665 was <b>Rank 15/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5964", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5964", status
            ),
            "Team 5964 was <b>Rank 21/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        es.step()  # QF schedule added
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 is <b>0-0-0</b> in the <b>Quarterfinals</b> as the <b>Captain</b> of <b>Alliance 1</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5240", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 is <b>0-0-0</b> in the <b>Quarterfinals</b> as the <b>1st Pick</b> of <b>Alliance 4</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc229", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc229", status
            ),
            "Team 229 is <b>0-0-0</b> in the <b>Quarterfinals</b> as the <b>2nd Pick</b> of <b>Alliance 2</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc1665", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1665", status
            ),
            "Team 1665 was <b>Rank 15/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5964", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5964", status
            ),
            "Team 5964 was <b>Rank 21/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        es.step()  # qf1m1
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 is <b>1-0-0</b> in the <b>Quarterfinals</b> as the <b>Captain</b> of <b>Alliance 1</b>.",
        )

        es.step()  # qf2m1
        es.step()  # qf3m1
        es.step()  # qf4m1
        es.step()  # qf1m2
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 is <b>0-0-0</b> in the <b>Semifinals</b> as the <b>Captain</b> of <b>Alliance 1</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5240", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 is <b>0-1-0</b> in the <b>Quarterfinals</b> as the <b>1st Pick</b> of <b>Alliance 4</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc229", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc229", status
            ),
            "Team 229 is <b>1-0-0</b> in the <b>Quarterfinals</b> as the <b>2nd Pick</b> of <b>Alliance 2</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc1665", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1665", status
            ),
            "Team 1665 was <b>Rank 15/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5964", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5964", status
            ),
            "Team 5964 was <b>Rank 21/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        es.step()  # qf2m2
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc5240", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 is <b>1-1-0</b> in the <b>Quarterfinals</b> as the <b>1st Pick</b> of <b>Alliance 4</b>.",
        )

        es.step()  # qf3m2
        es.step()  # qf4m2
        es.step()  # qf2m3
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc5240", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 is <b>0-0-0</b> in the <b>Semifinals</b> as the <b>1st Pick</b> of <b>Alliance 4</b>.",
        )

        es.step()  # qf4m3
        es.step()  # sf1m1
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 is <b>1-0-0</b> in the <b>Semifinals</b> as the <b>Captain</b> of <b>Alliance 1</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5240", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 is <b>0-1-0</b> in the <b>Semifinals</b> as the <b>1st Pick</b> of <b>Alliance 4</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc229", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc229", status
            ),
            "Team 229 is <b>0-0-0</b> in the <b>Semifinals</b> as the <b>2nd Pick</b> of <b>Alliance 2</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc1665", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1665", status
            ),
            "Team 1665 was <b>Rank 15/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5964", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5964", status
            ),
            "Team 5964 was <b>Rank 21/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        es.step()  # sf2m1
        es.step()  # sf1m2
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 is <b>0-0-0</b> in the <b>Finals</b> as the <b>Captain</b> of <b>Alliance 1</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5240", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 was <b>Rank 4/36</b> with a record of <b>9-3-0</b> in quals, competed in the playoffs as the <b>1st Pick</b> of <b>Alliance 4</b>, and was eliminated in the <b>Semifinals</b> with a playoff record of <b>2-3-0</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc229", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc229", status
            ),
            "Team 229 is <b>0-1-0</b> in the <b>Semifinals</b> as the <b>2nd Pick</b> of <b>Alliance 2</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc1665", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1665", status
            ),
            "Team 1665 was <b>Rank 15/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5964", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5964", status
            ),
            "Team 5964 was <b>Rank 21/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        es.step()  # sf2m2
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 is <b>0-0-0</b> in the <b>Finals</b> as the <b>Captain</b> of <b>Alliance 1</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5240", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 was <b>Rank 4/36</b> with a record of <b>9-3-0</b> in quals, competed in the playoffs as the <b>1st Pick</b> of <b>Alliance 4</b>, and was eliminated in the <b>Semifinals</b> with a playoff record of <b>2-3-0</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc229", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc229", status
            ),
            "Team 229 is <b>1-1-0</b> in the <b>Semifinals</b> as the <b>2nd Pick</b> of <b>Alliance 2</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc1665", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1665", status
            ),
            "Team 1665 is <b>1-1-0</b> in the <b>Semifinals</b> as the <b>Backup</b> of <b>Alliance 2</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5964", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5964", status
            ),
            "Team 5964 was <b>Rank 21/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        es.step()  # sf2m3
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 is <b>0-0-0</b> in the <b>Finals</b> as the <b>Captain</b> of <b>Alliance 1</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5240", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 was <b>Rank 4/36</b> with a record of <b>9-3-0</b> in quals, competed in the playoffs as the <b>1st Pick</b> of <b>Alliance 4</b>, and was eliminated in the <b>Semifinals</b> with a playoff record of <b>2-3-0</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc229", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc229", status
            ),
            "Team 229 is <b>0-0-0</b> in the <b>Finals</b> as the <b>2nd Pick</b> of <b>Alliance 2</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc1665", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1665", status
            ),
            "Team 1665 is <b>0-0-0</b> in the <b>Finals</b> as the <b>Backup</b> of <b>Alliance 2</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5964", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5964", status
            ),
            "Team 5964 was <b>Rank 21/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        es.step()  # f1m1
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 is <b>1-0-0</b> in the <b>Finals</b> as the <b>Captain</b> of <b>Alliance 1</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5240", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 was <b>Rank 4/36</b> with a record of <b>9-3-0</b> in quals, competed in the playoffs as the <b>1st Pick</b> of <b>Alliance 4</b>, and was eliminated in the <b>Semifinals</b> with a playoff record of <b>2-3-0</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc229", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc229", status
            ),
            "Team 229 is <b>0-1-0</b> in the <b>Finals</b> as the <b>2nd Pick</b> of <b>Alliance 2</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc1665", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1665", status
            ),
            "Team 1665 is <b>0-1-0</b> in the <b>Finals</b> as the <b>Backup</b> of <b>Alliance 2</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5964", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5964", status
            ),
            "Team 5964 was <b>Rank 21/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        es.step()  # f1m2
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 is <b>1-1-0</b> in the <b>Finals</b> as the <b>Captain</b> of <b>Alliance 1</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5240", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 was <b>Rank 4/36</b> with a record of <b>9-3-0</b> in quals, competed in the playoffs as the <b>1st Pick</b> of <b>Alliance 4</b>, and was eliminated in the <b>Semifinals</b> with a playoff record of <b>2-3-0</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc229", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc229", status
            ),
            "Team 229 is <b>1-1-0</b> in the <b>Finals</b> as the <b>2nd Pick</b> of <b>Alliance 2</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc1665", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1665", status
            ),
            "Team 1665 is <b>1-1-0</b> in the <b>Finals</b> as the <b>Backup</b> of <b>Alliance 2</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5964", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5964", status
            ),
            "Team 5964 was <b>Rank 21/36</b> with a record of <b>6-6-0</b> in quals.",
        )

        es.step()  # f1m3
        event = Event.get_by_id("2016nytr")
        status = EventTeamStatusHelper.generate_team_at_event_status("frc359", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 was <b>Rank 1/36</b> with a record of <b>11-1-0</b> in quals, competed in the playoffs as the <b>Captain</b> of <b>Alliance 1</b>, and <b>won the event</b> with a playoff record of <b>6-1-0</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5240", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 was <b>Rank 4/36</b> with a record of <b>9-3-0</b> in quals, competed in the playoffs as the <b>1st Pick</b> of <b>Alliance 4</b>, and was eliminated in the <b>Semifinals</b> with a playoff record of <b>2-3-0</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc229", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc229", status
            ),
            "Team 229 was <b>Rank 16/36</b> with a record of <b>6-6-0</b> in quals, competed in the playoffs as the <b>2nd Pick</b> of <b>Alliance 2</b>, and was eliminated in the <b>Finals</b> with a playoff record of <b>5-3-0</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc1665", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1665", status
            ),
            "Team 1665 was <b>Rank 15/36</b> with a record of <b>6-6-0</b> in quals, competed in the playoffs as the <b>Backup</b> of <b>Alliance 2</b>, and was eliminated in the <b>Finals</b> with a playoff record of <b>5-3-0</b>.",
        )

        status = EventTeamStatusHelper.generate_team_at_event_status("frc5964", event)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5964", status
            ),
            "Team 5964 was <b>Rank 21/36</b> with a record of <b>6-6-0</b> in quals.",
        )


@pytest.mark.usefixtures("ndb_context")
class Test2016nytrEventTeamStatusHelper(unittest.TestCase):
    maxDiff = None

    status_359 = {
        "alliance": {"backup": None, "name": "Alliance 1", "number": 1, "pick": 0},
        "playoff": {
            "current_level_record": {"losses": 1, "ties": 0, "wins": 2},
            "level": CompLevel.F,
            "playoff_type": PlayoffType.BRACKET_8_TEAM,
            "playoff_average": None,
            "record": {"losses": 1, "ties": 0, "wins": 6},
            "status": PlayoffOutcome.WON,
        },
        "last_match_key": "2016nytr_f1m3",
        "next_match_key": None,
        "qual": {
            "num_teams": 36,
            "ranking": {
                "dq": 0,
                "matches_played": 12,
                "qual_average": None,
                "rank": 1,
                "record": {"losses": 1, "ties": 0, "wins": 11},
                "sort_orders": [39.0, 310.0, 165.0, 448.0, 600.0],
                "team_key": "frc359",
            },
            "sort_order_info": [
                {"name": "Ranking Score", "precision": 0},
                {"name": "Auto", "precision": 0},
                {"name": "Scale/Challenge", "precision": 0},
                {"name": "Goals", "precision": 0},
                {"name": "Defense", "precision": 0},
            ],
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_5240 = {
        "alliance": {"backup": None, "name": "Alliance 4", "number": 4, "pick": 1},
        "playoff": {
            "current_level_record": {"losses": 2, "ties": 0, "wins": 0},
            "level": CompLevel.SF,
            "playoff_type": PlayoffType.BRACKET_8_TEAM,
            "playoff_average": None,
            "record": {"losses": 3, "ties": 0, "wins": 2},
            "status": PlayoffOutcome.ELIMINATED,
        },
        "last_match_key": "2016nytr_sf1m2",
        "next_match_key": None,
        "qual": {
            "num_teams": 36,
            "ranking": {
                "dq": 0,
                "matches_played": 12,
                "qual_average": None,
                "rank": 6,
                "record": {"losses": 3, "ties": 0, "wins": 9},
                "sort_orders": [28.0, 260.0, 150.0, 191.0, 575.0],
                "team_key": "frc5240",
            },
            "sort_order_info": [
                {"name": "Ranking Score", "precision": 0},
                {"name": "Auto", "precision": 0},
                {"name": "Scale/Challenge", "precision": 0},
                {"name": "Goals", "precision": 0},
                {"name": "Defense", "precision": 0},
            ],
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_229 = {
        "alliance": {
            "backup": {"in": "frc1665", "out": "frc229"},
            "name": "Alliance 2",
            "number": 2,
            "pick": 2,
        },
        "playoff": {
            "current_level_record": {"losses": 2, "ties": 0, "wins": 1},
            "level": CompLevel.F,
            "playoff_type": PlayoffType.BRACKET_8_TEAM,
            "playoff_average": None,
            "record": {"losses": 3, "ties": 0, "wins": 5},
            "status": PlayoffOutcome.ELIMINATED,
        },
        "last_match_key": "2016nytr_sf2m1",
        "next_match_key": None,
        "qual": {
            "num_teams": 36,
            "ranking": {
                "dq": 0,
                "matches_played": 12,
                "qual_average": None,
                "rank": 20,
                "record": {"losses": 6, "ties": 0, "wins": 6},
                "sort_orders": [20.0, 156.0, 130.0, 119.0, 525.0],
                "team_key": "frc229",
            },
            "sort_order_info": [
                {"name": "Ranking Score", "precision": 0},
                {"name": "Auto", "precision": 0},
                {"name": "Scale/Challenge", "precision": 0},
                {"name": "Goals", "precision": 0},
                {"name": "Defense", "precision": 0},
            ],
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_1665 = {
        "alliance": {
            "backup": {"in": "frc1665", "out": "frc229"},
            "name": "Alliance 2",
            "number": 2,
            "pick": -1,
        },
        "playoff": {
            "current_level_record": {"losses": 2, "ties": 0, "wins": 1},
            "level": CompLevel.F,
            "playoff_type": PlayoffType.BRACKET_8_TEAM,
            "playoff_average": None,
            "record": {"losses": 3, "ties": 0, "wins": 5},
            "status": PlayoffOutcome.ELIMINATED,
        },
        "last_match_key": "2016nytr_f1m3",
        "next_match_key": None,
        "qual": {
            "num_teams": 36,
            "ranking": {
                "dq": 0,
                "matches_played": 12,
                "qual_average": None,
                "rank": 18,
                "record": {"losses": 6, "ties": 0, "wins": 6},
                "sort_orders": [20.0, 192.0, 105.0, 146.0, 525.0],
                "team_key": "frc1665",
            },
            "sort_order_info": [
                {"name": "Ranking Score", "precision": 0},
                {"name": "Auto", "precision": 0},
                {"name": "Scale/Challenge", "precision": 0},
                {"name": "Goals", "precision": 0},
                {"name": "Defense", "precision": 0},
            ],
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_5964 = {
        "alliance": None,
        "playoff": None,
        "next_match_key": None,
        "last_match_key": "2016nytr_qm67",
        "qual": {
            "num_teams": 36,
            "ranking": {
                "dq": 0,
                "matches_played": 12,
                "qual_average": None,
                "rank": 23,
                "record": {"losses": 6, "ties": 0, "wins": 6},
                "sort_orders": [19.0, 218.0, 110.0, 159.0, 520.0],
                "team_key": "frc5964",
            },
            "sort_order_info": [
                {"name": "Ranking Score", "precision": 0},
                {"name": "Auto", "precision": 0},
                {"name": "Scale/Challenge", "precision": 0},
                {"name": "Goals", "precision": 0},
                {"name": "Defense", "precision": 0},
            ],
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_1124 = {"qual": None, "playoff": None, "alliance": None}

    def setUp(self):
        load_fixture(
            "test_data/fixtures/2016nytr_event_team_status.json",
            kind={"EventDetails": EventDetails, "Event": Event, "Match": Match},
            post_processor=self.eventKeyAdder,
        )
        self.event = Event.get_by_id("2016nytr")
        self.assertIsNotNone(self.event)

    def eventKeyAdder(self, obj):
        obj.event = ndb.Key(Event, "2016nytr")

    def test_event_winner(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc359", self.event
        )
        self.assertDictEqual(status, self.status_359)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 was <b>Rank 1/36</b> with a record of <b>11-1-0</b> in quals, competed in the playoffs as the <b>Captain</b> of <b>Alliance 1</b>, and <b>won the event</b> with a playoff record of <b>6-1-0</b>.",
        )
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_alliance_status_string(
                "frc259", status
            ),
            "<b>Captain</b> of <b>Alliance 1</b>",
        )
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_playoff_status_string(
                "frc259", status
            ),
            "<b>Won the event</b> with a playoff record of <b>6-1-0</b>",
        )

    def test_elim_semis_and_first_pick(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc5240", self.event
        )
        self.assertDictEqual(status, self.status_5240)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 was <b>Rank 6/36</b> with a record of <b>9-3-0</b> in quals, competed in the playoffs as the <b>1st Pick</b> of <b>Alliance 4</b>, and was eliminated in the <b>Semifinals</b> with a playoff record of <b>2-3-0</b>.",
        )
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_alliance_status_string(
                "frc5240", status
            ),
            "<b>1st Pick</b> of <b>Alliance 4</b>",
        )
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_playoff_status_string(
                "frc5240", status
            ),
            "<b>Eliminated in the Semifinals</b> with a playoff record of <b>2-3-0</b>",
        )

    def test_backup_out(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc229", self.event
        )
        self.assertDictEqual(status, self.status_229)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc229", status
            ),
            "Team 229 was <b>Rank 20/36</b> with a record of <b>6-6-0</b> in quals, competed in the playoffs as the <b>2nd Pick</b> of <b>Alliance 2</b>, and was eliminated in the <b>Finals</b> with a playoff record of <b>5-3-0</b>.",
        )
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_alliance_status_string(
                "frc229", status
            ),
            "<b>2nd Pick</b> of <b>Alliance 2</b>",
        )
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_playoff_status_string(
                "frc229", status
            ),
            "<b>Eliminated in the Finals</b> with a playoff record of <b>5-3-0</b>",
        )

    def test_backup_in(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc1665", self.event
        )
        self.assertDictEqual(status, self.status_1665)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1665", status
            ),
            "Team 1665 was <b>Rank 18/36</b> with a record of <b>6-6-0</b> in quals, competed in the playoffs as the <b>Backup</b> of <b>Alliance 2</b>, and was eliminated in the <b>Finals</b> with a playoff record of <b>5-3-0</b>.",
        )
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_alliance_status_string(
                "frc1665", status
            ),
            "<b>Backup</b> of <b>Alliance 2</b>",
        )
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_playoff_status_string(
                "frc1665", status
            ),
            "<b>Eliminated in the Finals</b> with a playoff record of <b>5-3-0</b>",
        )

    def test_team_not_picked(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc5964", self.event
        )
        self.assertDictEqual(status, self.status_5964)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5964", status
            ),
            "Team 5964 was <b>Rank 23/36</b> with a record of <b>6-6-0</b> in quals.",
        )
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_alliance_status_string(
                "frc5964", status
            ),
            "--",
        )
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_playoff_status_string(
                "frc5964", status
            ),
            "--",
        )


@pytest.mark.usefixtures("ndb_context")
class Test2016nytrEventTeamStatusHelperNoEventDetails(unittest.TestCase):
    maxDiff = None

    status_359 = {
        "alliance": None,
        "playoff": {
            "current_level_record": {"losses": 1, "ties": 0, "wins": 2},
            "level": CompLevel.F,
            "playoff_type": PlayoffType.BRACKET_8_TEAM,
            "playoff_average": None,
            "record": {"losses": 1, "ties": 0, "wins": 6},
            "status": PlayoffOutcome.WON,
        },
        "last_match_key": "2016nytr_f1m3",
        "next_match_key": None,
        "qual": {
            "num_teams": 36,
            "ranking": {
                "dq": None,
                "matches_played": 12,
                "qual_average": None,
                "rank": None,
                "record": {"losses": 1, "ties": 0, "wins": 11},
                "sort_orders": None,
                "team_key": "frc359",
            },
            "sort_order_info": None,
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_5240 = {
        "alliance": None,
        "playoff": {
            "current_level_record": {"losses": 2, "ties": 0, "wins": 0},
            "level": CompLevel.SF,
            "playoff_type": PlayoffType.BRACKET_8_TEAM,
            "playoff_average": None,
            "record": {"losses": 3, "ties": 0, "wins": 2},
            "status": PlayoffOutcome.ELIMINATED,
        },
        "last_match_key": "2016nytr_sf1m2",
        "next_match_key": None,
        "qual": {
            "num_teams": 36,
            "ranking": {
                "dq": None,
                "matches_played": 12,
                "qual_average": None,
                "rank": None,
                "record": {"losses": 3, "ties": 0, "wins": 9},
                "sort_orders": None,
                "team_key": "frc5240",
            },
            "sort_order_info": None,
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_229 = {
        "alliance": None,
        "playoff": {
            "current_level_record": {"losses": 2, "ties": 0, "wins": 1},
            "level": CompLevel.F,
            "playoff_type": PlayoffType.BRACKET_8_TEAM,
            "playoff_average": None,
            "record": {"losses": 3, "ties": 0, "wins": 5},
            "status": PlayoffOutcome.ELIMINATED,
        },
        "last_match_key": "2016nytr_sf2m1",
        "next_match_key": None,
        "qual": {
            "num_teams": 36,
            "ranking": {
                "dq": None,
                "matches_played": 12,
                "qual_average": None,
                "rank": None,
                "record": {"losses": 6, "ties": 0, "wins": 6},
                "sort_orders": None,
                "team_key": "frc229",
            },
            "sort_order_info": None,
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_1665 = {
        "alliance": None,
        "playoff": {
            "current_level_record": {"losses": 2, "ties": 0, "wins": 1},
            "level": CompLevel.F,
            "playoff_type": PlayoffType.BRACKET_8_TEAM,
            "playoff_average": None,
            "record": {"losses": 3, "ties": 0, "wins": 5},
            "status": PlayoffOutcome.ELIMINATED,
        },
        "last_match_key": "2016nytr_f1m3",
        "next_match_key": None,
        "qual": {
            "num_teams": 36,
            "ranking": {
                "dq": None,
                "matches_played": 12,
                "qual_average": None,
                "rank": None,
                "record": {"losses": 6, "ties": 0, "wins": 6},
                "sort_orders": None,
                "team_key": "frc1665",
            },
            "sort_order_info": None,
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_5964 = {
        "alliance": None,
        "playoff": None,
        "last_match_key": "2016nytr_qm67",
        "next_match_key": None,
        "qual": {
            "num_teams": 36,
            "ranking": {
                "dq": None,
                "matches_played": 12,
                "qual_average": None,
                "rank": None,
                "record": {"losses": 6, "ties": 0, "wins": 6},
                "sort_orders": None,
                "team_key": "frc5964",
            },
            "sort_order_info": None,
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_1124 = {"qual": None, "playoff": None, "alliance": None}

    def setUp(self):
        load_fixture(
            "test_data/fixtures/2016nytr_event_team_status.json",
            kind={"EventDetails": EventDetails, "Event": Event, "Match": Match},
            post_processor=self.eventKeyAdder,
        )
        self.event = Event.get_by_id("2016nytr")
        EventDetails.get_by_id("2016nytr").key.delete()  # Remove EventDetails
        self.assertIsNotNone(self.event)

    # Because I can't figure out how to get these to generate
    def eventKeyAdder(self, obj):
        obj.event = ndb.Key(Event, "2016nytr")

    def test_event_winner(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc359", self.event
        )
        self.assertDictEqual(status, self.status_359)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc359", status
            ),
            "Team 359 had a record of <b>11-1-0</b> in quals and <b>won the event</b> with a playoff record of <b>6-1-0</b>.",
        )

    def test_elim_semis_and_first_pick(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc5240", self.event
        )
        self.assertDictEqual(status, self.status_5240)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5240", status
            ),
            "Team 5240 had a record of <b>9-3-0</b> in quals and was eliminated in the <b>Semifinals</b> with a playoff record of <b>2-3-0</b>.",
        )

    def test_backup_out(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc229", self.event
        )
        self.assertDictEqual(status, self.status_229)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc229", status
            ),
            "Team 229 had a record of <b>6-6-0</b> in quals and was eliminated in the <b>Finals</b> with a playoff record of <b>5-3-0</b>.",
        )

    def test_backup_in(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc1665", self.event
        )
        self.assertDictEqual(status, self.status_1665)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1665", status
            ),
            "Team 1665 had a record of <b>6-6-0</b> in quals and was eliminated in the <b>Finals</b> with a playoff record of <b>5-3-0</b>.",
        )

    def testTeamNotPicked(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc5964", self.event
        )
        self.assertDictEqual(status, self.status_5964)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc5964", status
            ),
            "Team 5964 had a record of <b>6-6-0</b> in quals.",
        )


@pytest.mark.usefixtures("ndb_context")
class Test2016casjEventTeamStatusHelperNoEventDetails(unittest.TestCase):
    maxDiff = None

    status_254 = {
        "alliance": None,
        "playoff": {
            "current_level_record": {"losses": 0, "ties": 0, "wins": 2},
            "level": CompLevel.F,
            "playoff_type": PlayoffType.BRACKET_8_TEAM,
            "playoff_average": None,
            "record": {"losses": 0, "ties": 0, "wins": 6},
            "status": PlayoffOutcome.WON,
        },
        "last_match_key": "2016casj_f1m2",
        "next_match_key": None,
        "qual": {
            "num_teams": 64,
            "ranking": {
                "dq": None,
                "matches_played": 8,
                "qual_average": None,
                "rank": None,
                "record": {"losses": 0, "ties": 0, "wins": 8},
                "sort_orders": None,
                "team_key": "frc254",
            },
            "sort_order_info": None,
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    def setUp(self):
        load_fixture(
            "test_data/fixtures/2016casj.json",
            kind={"EventDetails": EventDetails, "Event": Event, "Match": Match},
            post_processor=self.eventKeyAdder,
        )
        self.event = Event.get_by_id("2016casj")
        self.assertIsNotNone(self.event)

    # Because I can't figure out how to get these to generate
    def eventKeyAdder(self, obj):
        obj.event = ndb.Key(Event, "2016casj")

    def test_event_surrogate(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc254", self.event
        )
        self.assertDictEqual(status, self.status_254)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc254", status
            ),
            "Team 254 had a record of <b>8-0-0</b> in quals and <b>won the event</b> with a playoff record of <b>6-0-0</b>.",
        )


@pytest.mark.usefixtures("ndb_context")
class Test2015casjEventTeamStatusHelper(unittest.TestCase):
    maxDiff = None

    status_254 = {
        "alliance": {"backup": None, "name": "Alliance 1", "number": 1, "pick": 0},
        "playoff": {
            "current_level_record": {"losses": 0, "ties": 0, "wins": 2},
            "level": CompLevel.F,
            "playoff_type": PlayoffType.AVG_SCORE_8_TEAM,
            "playoff_average": 224.14285714285714,
            "record": None,
            "status": PlayoffOutcome.WON,
        },
        "last_match_key": "2015casj_f1m2",
        "next_match_key": None,
        "qual": {
            "num_teams": 57,
            "ranking": {
                "dq": 0,
                "matches_played": 10,
                "qual_average": 200.4,
                "rank": 1,
                "record": None,
                "sort_orders": [200.4, 280.0, 200.0, 836.0, 522.0, 166.0],
                "team_key": "frc254",
            },
            "sort_order_info": [
                {"name": "Qual Avg.", "precision": 1},
                {"name": "Coopertition", "precision": 0},
                {"name": "Auto", "precision": 0},
                {"name": "Container", "precision": 0},
                {"name": "Tote", "precision": 0},
                {"name": "Litter", "precision": 0},
            ],
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_846 = {
        "alliance": {"backup": None, "name": "Alliance 3", "number": 3, "pick": 1},
        "playoff": {
            "current_level_record": None,
            "level": CompLevel.SF,
            "playoff_type": PlayoffType.AVG_SCORE_8_TEAM,
            "playoff_average": 133.59999999999999,
            "record": None,
            "status": PlayoffOutcome.ELIMINATED,
        },
        "last_match_key": "2015casj_sf1m5",
        "next_match_key": None,
        "qual": {
            "num_teams": 57,
            "ranking": {
                "dq": 0,
                "matches_played": 10,
                "qual_average": 97.0,
                "rank": 8,
                "record": None,
                "sort_orders": [97.0, 200.0, 20.0, 372.0, 294.0, 108.0],
                "team_key": "frc846",
            },
            "sort_order_info": [
                {"name": "Qual Avg.", "precision": 1},
                {"name": "Coopertition", "precision": 0},
                {"name": "Auto", "precision": 0},
                {"name": "Container", "precision": 0},
                {"name": "Tote", "precision": 0},
                {"name": "Litter", "precision": 0},
            ],
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_8 = {
        "alliance": None,
        "playoff": None,
        "last_match_key": "2015casj_qm92",
        "next_match_key": None,
        "qual": {
            "num_teams": 57,
            "ranking": {
                "dq": 0,
                "matches_played": 10,
                "qual_average": 42.6,
                "rank": 53,
                "record": None,
                "sort_orders": [42.6, 120.0, 0.0, 84.0, 150.0, 72.0],
                "team_key": "frc8",
            },
            "sort_order_info": [
                {"name": "Qual Avg.", "precision": 1},
                {"name": "Coopertition", "precision": 0},
                {"name": "Auto", "precision": 0},
                {"name": "Container", "precision": 0},
                {"name": "Tote", "precision": 0},
                {"name": "Litter", "precision": 0},
            ],
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_1124 = {"qual": None, "playoff": None, "alliance": None}

    def setUp(self):
        load_fixture(
            "test_data/fixtures/2015casj.json",
            kind={"EventDetails": EventDetails, "Event": Event, "Match": Match},
            post_processor=self.eventKeyAdder,
        )
        self.event = Event.get_by_id("2015casj")
        self.assertIsNotNone(self.event)

    # Because I can't figure out how to get these to generate
    def eventKeyAdder(self, obj):
        obj.event = ndb.Key(Event, "2015casj")

    def test_event_winner(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc254", self.event
        )
        self.assertDictEqual(status, self.status_254)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc254", status
            ),
            "Team 254 was <b>Rank 1/57</b> with an average score of <b>200.4</b> in quals, competed in the playoffs as the <b>Captain</b> of <b>Alliance 1</b>, and <b>won the event</b> with a playoff average of <b>224.1</b>.",
        )

    def test_elim_semis_and_first_pick(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc846", self.event
        )
        self.assertDictEqual(status, self.status_846)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc846", status
            ),
            "Team 846 was <b>Rank 8/57</b> with an average score of <b>97.0</b> in quals, competed in the playoffs as the <b>1st Pick</b> of <b>Alliance 3</b>, and was eliminated in the <b>Semifinals</b> with a playoff average of <b>133.6</b>.",
        )

    def test_team_not_picked(self):
        status = EventTeamStatusHelper.generate_team_at_event_status("frc8", self.event)
        self.assertDictEqual(status, self.status_8)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string("frc8", status),
            "Team 8 was <b>Rank 53/57</b> with an average score of <b>42.6</b> in quals.",
        )


@pytest.mark.usefixtures("ndb_context")
class Test2015casjEventTeamStatusHelperNoEventDetails(unittest.TestCase):
    maxDiff = None

    status_254 = {
        "alliance": None,
        "playoff": {
            "current_level_record": {"losses": 0, "ties": 0, "wins": 2},
            "level": CompLevel.F,
            "playoff_type": PlayoffType.AVG_SCORE_8_TEAM,
            "playoff_average": 224.14285714285714,
            "record": None,
            "status": PlayoffOutcome.WON,
        },
        "last_match_key": "2015casj_f1m2",
        "next_match_key": None,
        "qual": {
            "num_teams": 57,
            "ranking": {
                "dq": None,
                "matches_played": 10,
                "qual_average": 200.4,
                "rank": None,
                "record": None,
                "sort_orders": None,
                "team_key": "frc254",
            },
            "sort_order_info": None,
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_846 = {
        "alliance": None,
        "playoff": {
            "current_level_record": None,
            "level": CompLevel.SF,
            "playoff_type": PlayoffType.AVG_SCORE_8_TEAM,
            "playoff_average": 133.59999999999999,
            "record": None,
            "status": PlayoffOutcome.ELIMINATED,
        },
        "last_match_key": "2015casj_sf1m5",
        "next_match_key": None,
        "qual": {
            "num_teams": 57,
            "ranking": {
                "dq": None,
                "matches_played": 10,
                "qual_average": 97.0,
                "rank": None,
                "record": None,
                "sort_orders": None,
                "team_key": "frc846",
            },
            "sort_order_info": None,
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_8 = {
        "alliance": None,
        "playoff": None,
        "last_match_key": "2015casj_qm92",
        "next_match_key": None,
        "qual": {
            "num_teams": 57,
            "ranking": {
                "dq": None,
                "matches_played": 10,
                "qual_average": 42.6,
                "rank": None,
                "record": None,
                "sort_orders": None,
                "team_key": "frc8",
            },
            "sort_order_info": None,
            "status": EventTeamLevelStatus.COMPLETED,
        },
    }

    status_1124 = {"qual": None, "playoff": None, "alliance": None}

    def setUp(self):
        load_fixture(
            "test_data/fixtures/2015casj.json",
            kind={"EventDetails": EventDetails, "Event": Event, "Match": Match},
            post_processor=self.eventKeyAdder,
        )
        self.event = Event.get_by_id("2015casj")
        EventDetails.get_by_id("2015casj").key.delete()  # Remove EventDetails
        self.assertIsNotNone(self.event)

    # Because I can't figure out how to get these to generate
    def eventKeyAdder(self, obj):
        obj.event = ndb.Key(Event, "2015casj")

    def test_event_winner(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc254", self.event
        )
        self.assertDictEqual(status, self.status_254)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc254", status
            ),
            "Team 254 had an average score of <b>200.4</b> in quals and <b>won the event</b> with a playoff average of <b>224.1</b>.",
        )

    def test_elim_semis_and_first_pick(self):
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc846", self.event
        )
        self.assertDictEqual(status, self.status_846)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc846", status
            ),
            "Team 846 had an average score of <b>97.0</b> in quals and was eliminated in the <b>Semifinals</b> with a playoff average of <b>133.6</b>.",
        )

    def test_team_not_picked(self):
        status = EventTeamStatusHelper.generate_team_at_event_status("frc8", self.event)
        self.assertDictEqual(status, self.status_8)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string("frc8", status),
            "Team 8 had an average score of <b>42.6</b> in quals.",
        )


@pytest.mark.usefixtures("ndb_context")
class Test2022cmptxEventTeamStatusHelper(unittest.TestCase):
    maxDiff = None

    status_1619 = {
        "qual": None,
        "alliance": {
            "pick": 0,
            "name": "Galileo",
            "number": 3,
            "backup": None,
        },
        "playoff": {
            "playoff_type": 4,
            "status": PlayoffOutcome.WON,
            "level": CompLevel.F,
            "current_level_record": {"wins": 2, "losses": 1, "ties": 0},
            "record": {"wins": 5, "losses": 3, "ties": 0},
            "round_robin_rank": 2,
            "advanced_to_round_robin_finals": True,
        },
        "last_match_key": "2022cmptx_f1m3",
        "next_match_key": None,
    }

    status_4414 = {
        "qual": None,
        "alliance": {
            "pick": 1,
            "name": "Turing",
            "number": 2,
            "backup": None,
        },
        "playoff": {
            "playoff_type": 4,
            "status": PlayoffOutcome.ELIMINATED,
            "level": CompLevel.F,
            "current_level_record": {"wins": 1, "losses": 2, "ties": 0},
            "record": {"wins": 5, "losses": 3, "ties": 0},
            "round_robin_rank": 1,
            "advanced_to_round_robin_finals": True,
        },
        "last_match_key": "2022cmptx_f1m3",
        "next_match_key": None,
    }

    status_1323 = {
        "qual": None,
        "alliance": {
            "pick": 1,
            "name": "Carver",
            "number": 1,
            "backup": None,
        },
        "playoff": {
            "playoff_type": 4,
            "status": PlayoffOutcome.ELIMINATED,
            "level": CompLevel.SF,
            "current_level_record": {"wins": 2, "losses": 3, "ties": 0},
            "record": {"wins": 2, "losses": 3, "ties": 0},
            "round_robin_rank": 4,
            "advanced_to_round_robin_finals": False,
        },
        "last_match_key": "2022cmptx_sf1m13",
        "next_match_key": None,
    }

    status_4414_playing = {
        "qual": None,
        "alliance": {
            "pick": 1,
            "name": "Turing",
            "number": 2,
            "backup": None,
        },
        "playoff": {
            "playoff_type": 4,
            "status": PlayoffOutcome.PLAYING,
            "level": CompLevel.F,
            "current_level_record": {"wins": 1, "losses": 1, "ties": 0},
            "record": {"wins": 5, "losses": 2, "ties": 0},
            "round_robin_rank": 1,
            "advanced_to_round_robin_finals": True,
        },
        "last_match_key": "2022cmptx_f1m2",
        "next_match_key": "2022cmptx_f1m3",
    }

    status_1124 = {
        "qual": None,
        "alliance": None,
        "playoff": None,
        "last_match_key": None,
        "next_match_key": None,
    }

    def setUp(self) -> None:
        test_data_importer = JsonDataImporter()
        test_data_importer.import_event(__file__, "data/2022cmptx.json")
        test_data_importer.import_match_list(__file__, "data/2022cmptx_matches.json")
        test_data_importer.import_event_alliances(
            __file__, "data/2022cmptx_alliances.json", "2022cmptx"
        )

        self.event = Event.get_by_id("2022cmptx")

    def test_event_winner(self) -> None:
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc1619", self.event
        )

        self.assertDictEqual(status, self.status_1619)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1619", status
            ),
            "Team 1619 competed in the playoffs as the <b>Captain</b> of <b>Galileo</b> and <b>won the event</b> with a playoff record of <b>5-3-0</b>.",
        )

    def test_event_finalist(self) -> None:
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc4414", self.event
        )

        self.assertDictEqual(status, self.status_4414)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc4414", status
            ),
            "Team 4414 competed in the playoffs as the <b>1st Pick</b> of <b>Turing</b> and was eliminated in the <b>Finals</b> with a playoff record of <b>5-3-0</b>.",
        )

    def test_round_robin_eliminated(self) -> None:
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc1323", self.event
        )

        self.assertDictEqual(status, self.status_1323)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1323", status
            ),
            "Team 1323 competed in the playoffs as the <b>1st Pick</b> of <b>Carver</b> and was eliminated in the <b>Round Robin Bracket (Rank 4)</b> with a playoff record of <b>2-3-0</b>.",
        )

    def test_team_playing_in_finals(self) -> None:
        # Mark the last finals match as unplayed
        match = none_throws(Match.get_by_id("2022cmptx_f1m3"))
        alliances = match.alliances
        alliances[AllianceColor.RED]["score"] = -1
        alliances[AllianceColor.BLUE]["score"] = -1
        match.alliances = alliances
        match.put()
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc4414", self.event
        )

        self.assertDictEqual(status, self.status_4414_playing)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc4414", status
            ),
            "Team 4414 is <b>1-1-0</b> in the <b>Finals</b> as the <b>1st Pick</b> of <b>Turing</b>.",
        )

    def test_team_not_playing(self) -> None:
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc1124", self.event
        )

        self.assertDictEqual(status, self.status_1124)


@pytest.mark.usefixtures("ndb_context")
class Test2023njflaEventTeamStatusHelper(unittest.TestCase):
    maxDiff = None

    status_125 = {
        "qual": {
            "status": EventTeamLevelStatus.COMPLETED,
            "ranking": {
                "rank": None,
                "matches_played": 12,
                "dq": None,
                "record": {"wins": 10, "losses": 2, "ties": 0},
                "qual_average": None,
                "sort_orders": None,
                "team_key": "frc125",
            },
            "num_teams": 37,
            "sort_order_info": None,
        },
        "alliance": {
            "pick": 1,
            "name": "Alliance 2",
            "number": 2,
            "backup": None,
        },
        "playoff": {
            "playoff_type": 10,
            "status": PlayoffOutcome.WON,
            "level": CompLevel.F,
            "double_elim_round": DoubleElimRound.FINALS,
            "current_level_record": {"wins": 2, "losses": 0, "ties": 0},
            "record": {"wins": 5, "losses": 0, "ties": 0},
        },
        "last_match_key": "2023njfla_f1m2",
        "next_match_key": "2023njfla_f1m3",
    }

    status_11 = {
        "qual": {
            "status": EventTeamLevelStatus.COMPLETED,
            "ranking": {
                "rank": None,
                "matches_played": 12,
                "dq": None,
                "record": {"wins": 11, "losses": 1, "ties": 0},
                "qual_average": None,
                "sort_orders": None,
                "team_key": "frc11",
            },
            "num_teams": 37,
            "sort_order_info": None,
        },
        "alliance": {
            "pick": 0,
            "name": "Alliance 1",
            "number": 1,
            "backup": None,
        },
        "playoff": {
            "playoff_type": 10,
            "status": PlayoffOutcome.ELIMINATED,
            "level": CompLevel.F,
            "double_elim_round": DoubleElimRound.FINALS,
            "current_level_record": {"wins": 0, "losses": 2, "ties": 0},
            "record": {"wins": 3, "losses": 3, "ties": 0},
        },
        "last_match_key": "2023njfla_f1m2",
        "next_match_key": "2023njfla_f1m3",
    }

    status_1811 = {
        "qual": {
            "status": EventTeamLevelStatus.COMPLETED,
            "ranking": {
                "rank": None,
                "matches_played": 12,
                "dq": None,
                "record": {"wins": 7, "losses": 5, "ties": 0},
                "qual_average": None,
                "sort_orders": None,
                "team_key": "frc1811",
            },
            "num_teams": 37,
            "sort_order_info": None,
        },
        "alliance": {
            "pick": 0,
            "name": "Alliance 8",
            "number": 8,
            "backup": None,
        },
        "playoff": {
            "playoff_type": 10,
            "status": PlayoffOutcome.ELIMINATED,
            "level": CompLevel.SF,
            "double_elim_round": DoubleElimRound.ROUND4,
            "current_level_record": {"wins": 2, "losses": 2, "ties": 0},
            "record": {"wins": 2, "losses": 2, "ties": 0},
        },
        "last_match_key": "2023njfla_sf12m1",
        "next_match_key": None,
    }

    status_1923_unplayed = {
        "qual": {
            "status": EventTeamLevelStatus.COMPLETED,
            "ranking": {
                "rank": None,
                "matches_played": 12,
                "dq": None,
                "record": {"wins": 10, "losses": 2, "ties": 0},
                "qual_average": None,
                "sort_orders": None,
                "team_key": "frc1923",
            },
            "num_teams": 37,
            "sort_order_info": None,
        },
        "alliance": {
            "pick": 0,
            "name": "Alliance 2",
            "number": 2,
            "backup": None,
        },
        "playoff": {
            "playoff_type": 10,
            "status": PlayoffOutcome.PLAYING,
            "level": CompLevel.F,
            "double_elim_round": DoubleElimRound.FINALS,
            "current_level_record": {"wins": 1, "losses": 0, "ties": 0},
            "record": {"wins": 4, "losses": 0, "ties": 0},
        },
        "last_match_key": "2023njfla_f1m1",
        "next_match_key": "2023njfla_f1m2",
    }

    status_555 = {
        "qual": {
            "status": "completed",
            "ranking": {
                "rank": None,
                "matches_played": 12,
                "dq": None,
                "record": {"wins": 3, "losses": 9, "ties": 0},
                "qual_average": None,
                "sort_orders": None,
                "team_key": "frc555",
            },
            "num_teams": 37,
            "sort_order_info": None,
        },
        "alliance": None,
        "playoff": None,
        "last_match_key": "2023njfla_qm72",
        "next_match_key": None,
    }

    def setUp(self) -> None:
        test_data_importer = JsonDataImporter()
        test_data_importer.import_event(__file__, "data/2023njfla.json")
        test_data_importer.import_match_list(__file__, "data/2023njfla_matches.json")
        test_data_importer.import_event_alliances(
            __file__, "data/2023njfla_alliances.json", "2023njfla"
        )

        self.event = Event.get_by_id("2023njfla")

    def test_event_winner(self) -> None:
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc125", self.event
        )
        self.assertDictEqual(status, self.status_125)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc125", status
            ),
            "Team 125 had a record of <b>10-2-0</b> in quals, competed in the playoffs as the <b>1st Pick</b> of <b>Alliance 2</b>, and <b>won the event</b> with a playoff record of <b>5-0-0</b>.",
        )

    def test_event_finalist(self) -> None:
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc11", self.event
        )

        self.assertDictEqual(status, self.status_11)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string("frc11", status),
            "Team 11 had a record of <b>11-1-0</b> in quals, competed in the playoffs as the <b>Captain</b> of <b>Alliance 1</b>, and was eliminated in the <b>Finals</b> with a playoff record of <b>3-3-0</b>.",
        )

    def test_double_elim_eliminated(self) -> None:
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc1811", self.event
        )

        self.assertDictEqual(status, self.status_1811)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1811", status
            ),
            "Team 1811 had a record of <b>7-5-0</b> in quals, competed in the playoffs as the <b>Captain</b> of <b>Alliance 8</b>, and was eliminated in the <b>Double Elimination Bracket (Round 4)</b> with a playoff record of <b>2-2-0</b>.",
        )

    def test_team_playing_in_finals(self) -> None:
        # Mark the last finals match as unplayed
        match = none_throws(Match.get_by_id("2023njfla_f1m2"))
        alliances = match.alliances
        alliances[AllianceColor.RED]["score"] = -1
        alliances[AllianceColor.BLUE]["score"] = -1
        match.alliances = alliances
        match.put()

        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc1923", self.event
        )

        self.assertDictEqual(status, self.status_1923_unplayed)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc1923", status
            ),
            "Team 1923 is <b>1-0-0</b> in the <b>Finals</b> as the <b>Captain</b> of <b>Alliance 2</b>.",
        )

    def test_team_not_picked(self) -> None:
        status = EventTeamStatusHelper.generate_team_at_event_status(
            "frc555", self.event
        )

        self.assertDictEqual(status, self.status_555)
        self.assertEqual(
            EventTeamStatusHelper.generate_team_at_event_status_string(
                "frc555", status
            ),
            "Team 555 had a record of <b>3-9-0</b> in quals.",
        )
