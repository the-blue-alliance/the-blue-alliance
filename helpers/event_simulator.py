import copy
import datetime
import json

from appengine_fixture_loader.loader import load_fixture
from google.appengine.ext import ndb

from helpers.match_helper import MatchHelper
from models.event import Event
from models.event_details import EventDetails
from models.match import Match


class EventSimulator(object):
    """
    Steps through an event in time. At step = 0, only the Event exists:
    (step 0) Add all unplayed qual matches
    (step 1, substep n) Add results of each of the n qual matches +
        rankings being updated (if has_event_details)
    (step 2) Add alliance selections (if has_event_details)
    (step 3) Add unplayed QF matches
    (step 4, substep n) Add results of each of the n QF matches +
        update SF matches with advancing alliances (if not batch_advance) +
        update alliance selection backups (if has_event_details)
    (step 5) Add unplayed SF matches (if batch_advance)
    (step 6, substep n) Add results of each of the n SF matches +
        update F matches with advancing alliances (if not batch_advance) +
        update alliance selection backups (if has_event_details)
    (step 7) Add unplayed F matches (if batch_advance)
    (step 8, substep n) Add results of each of the n F matches +
        update alliance selection backups (if has_event_details)
    """
    def __init__(self, has_event_details=True, batch_advance=True):
        self._step = 0
        self._substep = 0
        # whether to update rankings and alliance selections
        self._has_event_details = has_event_details
        # whether to update next playoff level all at once, or as winners are determined
        self._batch_advance = batch_advance

        # Load and save complete data
        load_fixture('test_data/fixtures/2016nytr_event_team_status.json',
              kind={'EventDetails': EventDetails, 'Event': Event, 'Match': Match},
              post_processor=self._event_key_adder)
        event = Event.get_by_id('2016nytr')

        # Add 3rd matches that never got played
        Match(
            id='2016nytr_qf1m3',
            year=2016,
            event=event.key,
            comp_level='qf',
            set_number=1,
            match_number=3,
            alliances_json=json.dumps({
                'red': {
                    'teams': [],
                    'score': -1,
                },
                'blue': {
                    'teams': [],
                    'score': -1,
                }
            }),
            time=datetime.datetime(2016, 3, 19, 18, 34),
        ).put()
        Match(
            id='2016nytr_qf3m3',
            year=2016,
            event=event.key,
            comp_level='qf',
            set_number=3,
            match_number=3,
            alliances_json=json.dumps({
                'red': {
                    'teams': [],
                    'score': -1,
                },
                'blue': {
                    'teams': [],
                    'score': -1,
                }
            }),
            time=datetime.datetime(2016, 3, 19, 18, 48),
        ).put()

        self._event_detials = event.details
        self._played_matches = MatchHelper.organizeMatches(event.matches)

        # Delete data
        event.details.key.delete()
        ndb.delete_multi([match.key for match in event.matches])
        ndb.get_context().clear_cache()

    def _event_key_adder(self, obj):
        obj.event = ndb.Key(Event, '2016nytr')

    def step(self):
        event = Event.get_by_id('2016nytr')

        if self._step == 0:  # Qual match schedule added
            for match in copy.deepcopy(self._played_matches['qm']):
                for alliance in ['red', 'blue']:
                    match.alliances[alliance]['score'] = -1
                match.alliances_json = json.dumps(match.alliances)
                match.score_breakdown_json = None
                match.actual_time = None
                match.put()

            self._step += 1
        elif self._step == 1:  # After each qual match
            self._played_matches['qm'][self._substep].put()
            if self._substep < len(self._played_matches['qm']) - 1:
                self._substep += 1
            else:
                self._step += 1
                self._substep = 0
        elif self._step == 2:  # After alliance selections
            self._step += 1
        elif self._step == 3:  # QF schedule added
            for match in copy.deepcopy(self._played_matches['qf']):
                for alliance in ['red', 'blue']:
                    match.alliances[alliance]['score'] = -1
                match.alliances_json = json.dumps(match.alliances)
                match.score_breakdown_json = None
                match.actual_time = None
                match.put()

            self._step += 1
        elif self._step == 4:  # After each qf match
            MatchHelper.play_order_sort_matches(self._played_matches['qf'])[self._substep].put()
            if self._substep < len(self._played_matches['qf']) - 1:
                self._substep += 1
            else:
                self._step += 1
                self._substep = 0

        ndb.get_context().clear_cache()
