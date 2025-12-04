import datetime

from google.appengine.ext import ndb
from typing_extensions import TypedDict

from backend.common.models.event import Event
from backend.common.models.keys import MatchKey, TeamKey


class ZebraTeamData(TypedDict):
    team_key: TeamKey
    xs: list[float | None]
    ys: list[float | None]


class ZebraAllianceData(TypedDict):
    red: list[ZebraTeamData]
    blue: list[ZebraTeamData]


class ZebraData(TypedDict):
    key: MatchKey
    times: list[float]
    alliances: ZebraAllianceData


class ZebraMotionWorks(ndb.Model):
    """
    The ZebraMotionWorks model represents robot tracking data from the
    Zebra MotionWorks system
    """

    event: ndb.Key = ndb.KeyProperty(kind=Event, required=True)
    data: list[ZebraData] = ndb.JsonProperty(required=True)

    created = ndb.DateTimeProperty(
        auto_now_add=True, indexed=False, default=datetime.datetime.fromtimestamp(0)
    )
    updated = ndb.DateTimeProperty(
        auto_now=True, indexed=False, default=datetime.datetime.fromtimestamp(0)
    )
