from datetime import datetime
from typing import Any, Dict, Optional

import requests

from backend.common.manipulators.award_manipulator import AwardManipulator
from backend.common.manipulators.district_manipulator import DistrictManipulator
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.award import Award
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, MatchKey, TeamKey
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.queries.dict_converters.award_converter import AwardConverter
from backend.common.queries.dict_converters.district_converter import DistrictConverter
from backend.common.queries.dict_converters.event_converter import EventConverter
from backend.common.queries.dict_converters.match_converter import MatchConverter
from backend.common.queries.dict_converters.media_converter import MediaConverter
from backend.common.queries.dict_converters.team_converter import TeamConverter


class LocalDataBootstrap:
    AUTH_HEADER = "X-TBA-Auth-Key"

    @classmethod
    def store_district(cls, data: Dict) -> District:
        district = DistrictConverter.dictToModel_v3(data)

        return DistrictManipulator.createOrUpdate(district)

    @classmethod
    def store_event(cls, data: Dict) -> Event:
        event = EventConverter.dictToModel_v3(data)
        EventManipulator.createOrUpdate(event)

        cls.store_district(data["district"]) if data["district"] else None
        return event

    @staticmethod
    def store_team(data: Dict) -> Team:
        team = TeamConverter.dictToModel_v3(data)

        return TeamManipulator.createOrUpdate(team)

    @staticmethod
    def store_team_media(
        data: Dict, year: Optional[int], team_key: Optional[TeamKey]
    ) -> Media:
        media = MediaConverter.dictToModel_v3(data, year, team_key)

        return MediaManipulator.createOrUpdate(media)

    @classmethod
    def store_match(cls, data: Dict) -> Match:
        match = MatchConverter.dictToModel_v3(data)

        return MatchManipulator.createOrUpdate(match)

    @staticmethod
    def store_eventteam(team: Team, event: Event) -> EventTeam:
        eventteam = EventTeam(id="{}_{}".format(event.key_name, team.key_name))
        eventteam.event = event.key
        eventteam.team = team.key
        eventteam.year = event.year

        return EventTeamManipulator.createOrUpdate(eventteam)

    @classmethod
    def store_eventdetail(
        cls, event: Event, detail_type: str, data: Any
    ) -> EventDetails:
        detail = EventDetails.get_or_insert(event.key_name)
        setattr(detail, detail_type, data)

        return EventDetailsManipulator.createOrUpdate(detail)

    @classmethod
    def store_award(cls, data: Dict, event: Event) -> Award:
        award = AwardConverter.dictToModel_v3(data, event)

        return AwardManipulator.createOrUpdate(award)

    @classmethod
    def fetch_endpoint(cls, endpoint: str, auth_token: str) -> Dict:
        full_url = f"https://www.thebluealliance.com/api/v3/{endpoint}"
        r = requests.get(
            full_url, headers={cls.AUTH_HEADER: auth_token, "User-agent": "Mozilla/5.0"}
        )
        return r.json()

    @classmethod
    def fetch_team(cls, team_key: TeamKey, auth_token: str) -> Dict:
        return cls.fetch_endpoint(f"team/{team_key}", auth_token)

    @classmethod
    def fetch_team_media(cls, team_key: TeamKey, year: int, auth_token: str) -> Dict:
        return cls.fetch_endpoint(f"team/{team_key}/media/{year}", auth_token)

    @classmethod
    def fetch_event(cls, event_key: EventKey, auth_token: str) -> Dict:
        return cls.fetch_endpoint(f"event/{event_key}", auth_token)

    @classmethod
    def fetch_match(cls, match_key: MatchKey, auth_token: str) -> Dict:
        return cls.fetch_endpoint(f"match/{match_key}", auth_token)

    @classmethod
    def fetch_event_detail(
        cls, event_key: EventKey, detail: str, auth_token: str
    ) -> Dict:
        return cls.fetch_endpoint(f"event/{event_key}/{detail}", auth_token)

    @classmethod
    def update_event(cls, key: EventKey, auth_token: str) -> None:
        event_data = cls.fetch_event(key, auth_token)
        event = cls.store_event(event_data)

        event_teams = cls.fetch_event_detail(key, "teams", auth_token)
        teams = list(map(cls.store_team, event_teams))
        list(map(lambda t: cls.store_eventteam(t, event), teams))

        event_matches = cls.fetch_event_detail(key, "matches", auth_token)
        list(map(cls.store_match, event_matches))

        event_rankings = cls.fetch_event_detail(key, "rankings", auth_token)
        cls.store_eventdetail(
            event, "rankings2", event_rankings["rankings"] if event_rankings else []
        )

        event_alliances = cls.fetch_event_detail(key, "alliances", auth_token)
        cls.store_eventdetail(event, "alliance_selections", event_alliances)

        event_awards = cls.fetch_event_detail(key, "awards", auth_token)
        list(map(lambda t: cls.store_award(t, event), event_awards))

        event_predictions = cls.fetch_event_detail(key, "predictions", auth_token)
        cls.store_eventdetail(event, "predictions", event_predictions)

    @classmethod
    def bootstrap_key(cls, key: str, apiv3_key: str) -> Optional[str]:
        if Match.validate_key_name(key):
            match_data = cls.fetch_match(key, apiv3_key)
            cls.store_match(match_data)
            return f"/match/{key}"
        elif Event.validate_key_name(key):
            cls.update_event(key, apiv3_key)
            return f"/event/{key}"
        elif Team.validate_key_name(key):
            team_data = cls.fetch_team(key, apiv3_key)
            cls.store_team(team_data)

            year = datetime.now().year
            for media in cls.fetch_team_media(key, year, apiv3_key):
                cls.store_team_media(media, year, key)

            return f"/team/{key[3:]}"
        elif key.isdigit():
            event_keys = [
                event["key"] for event in cls.fetch_endpoint(f"events/{key}", apiv3_key)
            ]
            for event in event_keys:
                cls.update_event(event, apiv3_key)
            return f"/events/{key}"
        else:
            return None
