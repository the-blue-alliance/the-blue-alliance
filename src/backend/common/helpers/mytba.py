from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from itertools import groupby
from typing import cast, Dict, List, Optional, Set, Type

from google.appengine.ext import ndb

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.model_type import ModelType
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.favorite import Favorite
from backend.common.models.keys import EventKey
from backend.common.models.match import Match
from backend.common.models.mytba import MyTBAModel
from backend.common.models.subscription import Subscription
from backend.common.models.team import Team
from backend.common.models.wlt import WLTRecord
from backend.common.queries.match_query import EventMatchesQuery


@dataclass
class AttendanceStatsHelper:
    event_teams: List[EventTeam]
    events: List[Event]
    teams: List[Team]
    matches: Dict[EventKey, List[Match]]

    @property
    def event_count(self) -> int:
        return len(self.events)

    @property
    def total_days(self) -> int:
        return sum(
            (
                (obj.end_date - obj.start_date).days + 1
                for obj in self.events
                if obj.start_date and obj.end_date
            ),
        )

    @property
    def total_matches(self) -> int:
        return sum(len(matches) for matches in self.matches.values())

    @cached_property
    def record(self) -> WLTRecord:
        wlt = WLTRecord(wins=0, losses=0, ties=0)
        for event_team_key, matches in self.matches.items():
            _, team = event_team_key.split("_")

            for match in matches:
                if match.winning_alliance == "":
                    wlt["ties"] += 1
                else:
                    alliance = match.alliances[
                        cast(AllianceColor, match.winning_alliance)
                    ]
                    if team in alliance["teams"]:
                        wlt["wins"] += 1
                    else:
                        wlt["losses"] += 1

        return wlt

    @property
    def winrate(self) -> float:
        record = self.record
        return (
            100
            * record["wins"]
            / max(1, record["wins"] + record["losses"] + record["ties"])
        )


@dataclass
class MyTBA:
    """A wrapper object for a collection of myTBA models for a given user"""

    def __init__(self, models: List[MyTBAModel]) -> None:
        self.models = models

    @property
    def event_models(self) -> List[MyTBAModel]:
        return [model for model in self.models if model.model_type == ModelType.EVENT]

    @staticmethod
    def _event_keys(models: List[MyTBAModel]) -> Set[ndb.Key]:
        return {ndb.Key(Event, model.model_key) for model in models}

    @property
    def events(self) -> List[Event]:
        event_models = self.event_models
        wildcard_event_models = [m for m in event_models if m.is_wildcard]

        event_keys = MyTBA._event_keys([m for m in event_models if not m.is_wildcard])
        futures = ndb.get_multi_async(event_keys)
        events = [f.get_result() for f in futures]

        # Add dummy Event models for wildcard events - for render purposes
        for model in wildcard_event_models:
            event_year = int(model.model_key[:-1])
            events.append(
                Event(
                    id=model.model_key,
                    short_name="ALL EVENTS",
                    event_short=model.model_key,
                    year=event_year,
                    start_date=datetime(event_year, 1, 1),
                    end_date=datetime(event_year, 1, 1),
                )
            )

        return events

    @property
    def team_models(self) -> List[MyTBAModel]:
        return [model for model in self.models if model.model_type == ModelType.TEAM]

    @property
    def teams(self) -> List[Team]:
        team_keys = {ndb.Key(Team, model.model_key) for model in self.team_models}
        futures = ndb.get_multi_async(team_keys)
        return [f.get_result() for f in futures]

    @property
    def match_models(self) -> List[MyTBAModel]:
        return [model for model in self.models if model.model_type == ModelType.MATCH]

    @property
    def matches(self) -> List[Match]:
        match_keys = {ndb.Key(Match, model.model_key) for model in self.match_models}
        futures = ndb.get_multi_async(match_keys)
        return [f.get_result() for f in futures]

    @property
    def event_matches(self) -> Dict[ndb.Key, List[Match]]:
        # Key is an Event key, value is a list of Matches for that Event
        return {
            group[0]: [match for match in group[1]]
            for group in groupby(self.matches, key=lambda x: x.event)
        }

    @property
    def event_teams_models(self) -> List[MyTBAModel]:
        return [
            model for model in self.models if model.model_type == ModelType.EVENT_TEAM
        ]

    @property
    def event_teams(self) -> List[EventTeam]:
        event_team_keys = {
            ndb.Key(EventTeam, model.model_key) for model in self.event_teams_models
        }
        futures = ndb.get_multi_async(event_team_keys)
        return [f.get_result() for f in futures]

    @property
    def attendance_stats_helper(self) -> AttendanceStatsHelper:
        event_teams = self.event_teams
        team_futures = ndb.get_multi_async(
            {event_team.team for event_team in event_teams}
        )
        event_futures = ndb.get_multi_async(
            {event_team.event for event_team in event_teams}
        )

        teams = sorted(
            [f.get_result() for f in team_futures], key=lambda t: t.team_number
        )
        events = sorted(
            [f.get_result() for f in event_futures], key=lambda e: e.end_date
        )

        matches_futures = {
            event.key.string_id(): EventMatchesQuery(
                event_key=event.key.string_id()
            ).fetch_async()
            for event in events
        }
        matches = {k: v.get_result() for k, v in matches_futures.items()}
        event_team_matches: Dict[EventKey, List[Match]] = {}
        for event_team in event_teams:
            if event_team.key_name not in event_team_matches:
                event_team_matches[event_team.key_name] = []

            for match in matches[event_team.event.string_id()]:
                for team_key in match.team_keys:
                    if team_key.string_id() == event_team.team.string_id():
                        event_team_matches[event_team.key_name].append(match)

        return AttendanceStatsHelper(
            event_teams=event_teams,
            events=events,
            teams=teams,
            matches=event_team_matches,
        )

    def favorite(self, model_type: ModelType, model_key: str) -> Optional[Favorite]:
        return self._first_model(Favorite, model_type, model_key)  # pyre-ignore[7]

    def subscription(
        self, model_type: ModelType, model_key: str
    ) -> Optional[Subscription]:
        return self._first_model(Subscription, model_type, model_key)  # pyre-ignore[7]

    def _first_model(
        self,
        mytba_model_type: Type[MyTBAModel],
        model_type: ModelType,
        model_key: str,
    ) -> Optional[MyTBAModel]:
        # Note: There's probably a way to do this where mytba_model_type is a Generic Type and the return
        # is that Type. But I couldn't figure it out.
        # ~ zach
        return next(
            iter(
                [
                    model
                    for model in self.models
                    if isinstance(model, mytba_model_type)
                    if model.model_type == model_type and model.model_key == model_key
                ]
            ),
            None,
        )
