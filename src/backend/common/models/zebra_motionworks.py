import datetime
from typing import List, Optional, TypedDict

from google.cloud import ndb

from backend.common.models.event import Event
from backend.common.models.keys import MatchKey, TeamKey


class ZebraTeamData(TypedDict):
    team_key: TeamKey
    xs: List[Optional[float]]
    ys: List[Optional[float]]


class ZebraAllianceData(TypedDict):
    red: List[ZebraTeamData]
    blue: List[ZebraTeamData]


class ZebraData(TypedDict):
    key: MatchKey
    times: List[float]
    alliances: ZebraAllianceData


class ZebraMotionWorks(ndb.Model):
    """
    The ZebraMotionWorks model represents robot tracking data from the
    Zebra MotionWorks system
    """

    event: ndb.Key = ndb.KeyProperty(kind=Event, required=True)
    data: List[ZebraData] = ndb.JsonProperty(required=True)

    created = ndb.DateTimeProperty(
        auto_now_add=True, indexed=False, default=datetime.datetime.fromtimestamp(0)
    )
    updated = ndb.DateTimeProperty(
        auto_now=True, indexed=False, default=datetime.datetime.fromtimestamp(0)
    )
