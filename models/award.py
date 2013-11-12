import json

from google.appengine.ext import ndb

from consts.award_type import AwardType

from models.event import Event
from models.team import Team


class Award(ndb.Model):
    """
    Awards represent FIRST Robotics Competition awards given out at an event.
    key_name is formatted as: <event_key_name>_<award_type_enum>
    If multiple recipients win the same award at the same event (such as
    Winner or Dean's List), they show up under the repeated properties.
    """

    name_str = ndb.StringProperty(required=True, indexed=False)  # award name that shows up on USFIRST Pages. May vary for the same award type.
    award_type_enum = ndb.IntegerProperty(required=True)
    year = ndb.IntegerProperty(required=True)  # year the award was awarded
    event = ndb.KeyProperty(kind=Event, required=True)  # event at which the award was awarded
    event_type_enum = ndb.IntegerProperty(required=True)  # needed to query for awards from events of a certain event type

    team_list = ndb.KeyProperty(kind=Team, repeated=True)  # key of team(s) that won the award (if applicable)
    recipient_json_list = ndb.StringProperty(repeated=True)  # JSON dict(s) with team_number and/or awardee

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        self._recipient_list = None
        super(Award2, self).__init__(*args, **kw)

    @property
    def recipient_list(self):
        if self._recipient_list is None:
            self._recipient_list = []
            for recipient_json in self.recipient_json_list:
                self._recipient_list.append(json.loads(recipient_json))
        return self._recipient_list

    @property
    def key_name(self):
        return self.render_key_name(self.event.id(), self.award_type_enum)

    @classmethod
    def render_key_name(self, event_key_name, award_type_enum):
        return '{}_{}'.format(event_key_name, award_type_enum)
