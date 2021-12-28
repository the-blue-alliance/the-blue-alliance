from dataclasses import dataclass
from datetime import datetime
from itertools import groupby
from typing import Dict, List, Optional, Set, Type

from google.appengine.ext import ndb

from backend.common.consts.model_type import ModelType
from backend.common.models.event import Event
from backend.common.models.favorite import Favorite
from backend.common.models.match import Match
from backend.common.models.mytba import MyTBAModel
from backend.common.models.subscription import Subscription
from backend.common.models.team import Team


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
                    if type(model) == mytba_model_type
                    if model.model_type == model_type and model.model_key == model_key
                ]
            ),
            None,
        )
