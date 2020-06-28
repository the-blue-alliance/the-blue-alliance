import json
from typing import Dict, List, Optional

from google.cloud import ndb
from pyre_extensions import none_throws, safe_cast

from backend.common.consts import award_type, event_type
from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.models.award_recipient import AwardRecipient
from backend.common.models.event import Event
from backend.common.models.keys import AwardKey, EventKey, Year
from backend.common.models.team import Team


class Award(ndb.Model):
    """
    Awards represent FIRST Robotics Competition awards given out at an event.
    key_name is formatted as: <event_key_name>_<award_type_enum>
    If multiple recipients win the same award at the same event (such as
    Winner or Dean's List), they show up under the repeated properties.
    """

    name_str = ndb.TextProperty(
        required=True, indexed=False
    )  # award name that shows up on USFIRST Pages. May vary for the same award type.
    award_type_enum: AwardType = safe_cast(
        AwardType, ndb.IntegerProperty(required=True, choices=award_type.AWARD_TYPES)
    )
    year: Year = ndb.IntegerProperty(required=True)  # year the award was awarded
    event = ndb.KeyProperty(
        kind=Event, required=True
    )  # event at which the award was awarded
    event_type_enum = ndb.IntegerProperty(
        required=True, choices=event_type.EVENT_TYPES,
    )  # needed to query for awards from events of a certain event type

    team_list = ndb.KeyProperty(
        kind=Team, repeated=True
    )  # key of team(s) that won the award (if applicable)
    recipient_json_list = ndb.StringProperty(
        repeated=True
    )  # JSON dict(s) with team_number and/or awardee

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {
            "event": set(),
            "team_list": set(),
            "year": set(),
            "event_type_enum": set(),
            "award_type_enum": set(),
        }
        self._recipient_list: Optional[List[AwardRecipient]] = None
        self._recipient_dict: Optional[Dict[Optional[int], List[AwardRecipient]]] = None
        self._recipient_list_json: Optional[str] = None
        super(Award, self).__init__(*args, **kw)

    @property
    def is_blue_banner(self) -> bool:
        return self.award_type_enum in award_type.BLUE_BANNER_AWARDS

    @property
    def count_banner(self) -> bool:
        if (
            self.award_type_enum == AwardType.WOODIE_FLOWERS
            and self.event_type_enum == EventType.CMP_FINALS
            and self.year >= 2017
        ):
            # Only count WFA banner from the first Championship
            # (for insights purposes)
            cmp_event_keys = (
                Event.query(
                    Event.year == self.year,
                    Event.event_type_enum == EventType.CMP_FINALS,
                )
                .order(Event.start_date)
                .fetch(keys_only=True)
            )
            if cmp_event_keys and cmp_event_keys[0] != self.event:
                return False
        return True

    @property
    def normalized_name(self) -> str:
        if self.award_type_enum in award_type.NORMALIZED_NAMES:
            if (
                self.event_type_enum
                in award_type.NORMALIZED_NAMES[self.award_type_enum]
            ):
                return award_type.NORMALIZED_NAMES[self.award_type_enum][
                    self.event_type_enum
                ]
            else:
                return award_type.NORMALIZED_NAMES[self.award_type_enum][None]
        else:
            return self.name_str

    @property
    def recipient_dict(self) -> Dict[Optional[int], List[AwardRecipient]]:
        """
        Uses recipient_list to add a recipient_dict property,
        where the key is the team_number and the value is a list of awardees.
        """
        if self._recipient_dict is None:
            recipient_dict = {}
            for recipient in self.recipient_list:
                team_number = recipient["team_number"]
                awardee = recipient["awardee"]
                if team_number in recipient_dict:
                    recipient_dict[team_number].append(awardee)
                else:
                    recipient_dict[team_number] = [awardee]
            self._recipient_dict = recipient_dict
        return none_throws(self._recipient_dict)

    @property
    def recipient_list(self) -> List[AwardRecipient]:
        if self._recipient_list is None:
            recipient_list = []
            for recipient_json in self.recipient_json_list:
                recipient_list.append(json.loads(recipient_json))
            self._recipient_list = recipient_list
        return none_throws(self._recipient_list)

    @property
    def recipient_list_json(self) -> str:
        """
        A JSON version of the recipient_list
        """
        if self._recipient_list_json is None:
            self._recipient_list_json = json.dumps(self.recipient_list)

        return none_throws(self._recipient_list_json)

    @property
    def key_name(self) -> AwardKey:
        return self.render_key_name(self.event.id(), self.award_type_enum)

    @classmethod
    def render_key_name(
        cls, event_key_name: EventKey, award_type_enum: AwardType
    ) -> AwardKey:
        return "{}_{}".format(event_key_name, award_type_enum)

    @classmethod
    def validate_key_name(cls, key: str) -> bool:
        split = key.split("_")
        return (
            len(split) == 2
            and Event.validate_key_name(split[0])
            and split[1].isnumeric()
            and int(split[1]) in AwardType.__members__.values()
        )
