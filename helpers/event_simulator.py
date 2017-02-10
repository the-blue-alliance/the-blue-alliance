import json
from appengine_fixture_loader.loader import load_fixture
from google.appengine.ext import ndb

from models.event import Event
from models.event_details import EventDetails
from models.match import Match


class EventSimulator(object):
    """
    Steps through an event in time. At step = 0, only the Event exists:
    (1) Add all unplayed qual matches
    (n) Add results of each of the n qual matches +
        rankings being updated (if has_event_details)
    (1) Add alliance selections (if has_event_details)
    (1) Add unplayed QF matches
    (n) Add results of each of the n QF matches +
        update SF matches with advancing alliances (if not batch_advance) +
        update alliance selection backups (if has_event_details)
    (1) Add unplayed SF matches (if batch_advance)
    (n) Add results of each of the n SF matches +
        update F matches with advancing alliances (if not batch_advance) +
        update alliance selection backups (if has_event_details)
    (1) Add unplayed F matches (if batch_advance)
    (n) Add results of each of the n F matches +
        update alliance selection backups (if has_event_details)
    """
    def __init__(self, has_event_details=True, batch_advance=True):
        self._step = 0
        # whether to update rankings and alliance selections
        self._has_event_details = has_event_details
        # whether to update next playoff level all at once, or as winners are determined
        self._batch_advance = batch_advance
        self.step()

    def _reload_all(self):
        load_fixture('test_data/fixtures/2016nytr_event_team_status.json',
              kind={'EventDetails': EventDetails, 'Event': Event, 'Match': Match},
              post_processor=self._event_key_adder)

    def _event_key_adder(self, obj):
        obj.event = ndb.Key(Event, '2016nytr')

    def step(self):
        self._reload_all()
        event = Event.get_by_id('2016nytr')

        if self._step == 0:  # Before anything has happened
            event.details.key.delete()
            ndb.delete_multi([match.key for match in event.matches])
        elif self._step == 1:  # Qual match schedule added
            event.details.key.delete()
            for match in event.matches:
                if match.comp_level == 'qm':
                    for alliance in ['red', 'blue']:
                        match.alliances[alliance]['score'] = -1
                    match.alliances_json = json.dumps(match.alliances)
                    match.score_breakdown_json = None
                    match.actual_time = None
                    match.put()
                else:
                    match.key.delete()

        ndb.get_context().clear_cache()
        self._step += 1
