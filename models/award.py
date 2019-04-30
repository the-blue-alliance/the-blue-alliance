import json

from google.appengine.ext import ndb

from consts.award_type import AwardType
from consts.event_type import EventType
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
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            'event': set(),
            'team_list': set(),
            'year': set(),
            'event_type_enum': set(),
            'award_type_enum': set(),
        }
        self._recipient_list = None
        self._recipient_dict = None
        self._recipient_list_json = None
        super(Award, self).__init__(*args, **kw)

    @property
    def is_blue_banner(self):
        return self.award_type_enum in AwardType.BLUE_BANNER_AWARDS

    @property
    def count_banner(self):
        if (self.award_type_enum == AwardType.WOODIE_FLOWERS and
                self.event_type_enum == EventType.CMP_FINALS and
                self.year >= 2017):
            # Only count WFA banner from the first Championship
            cmp_event_keys = Event.query(
                Event.year == self.year,
                Event.event_type_enum == EventType.CMP_FINALS
            ).order(Event.start_date).fetch(keys_only=True)
            if cmp_event_keys and cmp_event_keys[0] != self.event:
                return False
        return True

    @property
    def normalized_name(self):
        if self.award_type_enum in AwardType.normalized_name:
            if self.event_type_enum in AwardType.normalized_name[self.award_type_enum]:
                return AwardType.normalized_name[self.award_type_enum][self.event_type_enum]
            else:
                return AwardType.normalized_name[self.award_type_enum][None]
        else:
            return self.name_str

    @property
    def recipient_dict(self):
        """
        Uses recipient_list to add a recipient_dict property,
        where the key is the team_number and the value is a list of awardees.
        """
        if self._recipient_dict is None:
            self._recipient_dict = {}
            for recipient in self.recipient_list:
                team_number = recipient['team_number']
                awardee = recipient['awardee']
                if team_number in self._recipient_dict:
                    self._recipient_dict[team_number].append(awardee)
                else:
                    self._recipient_dict[team_number] = [awardee]
        return self._recipient_dict

    @property
    def recipient_list(self):
        if self._recipient_list is None:
            self._recipient_list = []
            for recipient_json in self.recipient_json_list:
                self._recipient_list.append(json.loads(recipient_json))
        return self._recipient_list

    @property
    def recipient_list_json(self):
        """
        A JSON version of the recipient_list
        """
        if self._recipient_list_json is None:
            self._recipient_list_json = json.dumps(self.recipient_list)

        return self._recipient_list_json

    @property
    def key_name(self):
        return self.render_key_name(self.event.id(), self.award_type_enum)

    @classmethod
    def render_key_name(self, event_key_name, award_type_enum):
        return '{}_{}'.format(event_key_name, award_type_enum)
