from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Callable, cast, Dict, List, Optional, Union

import requests
from google.appengine.ext import ndb

from backend.common.consts.renamed_districts import ALL_KNOWN_DISTRICT_ABBREVIATIONS
from backend.common.helpers.deferred import defer_safe
from backend.common.helpers.listify import listify
from backend.common.manipulators.award_manipulator import AwardManipulator
from backend.common.manipulators.district_manipulator import DistrictManipulator
from backend.common.manipulators.district_team_manipulator import (
    DistrictTeamManipulator,
)
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
from backend.common.models.district_ranking import DistrictRanking
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_team import EventTeam
from backend.common.models.event_team_pit_location import EventTeamPitLocation
from backend.common.models.keys import (
    DistrictAbbreviation,
    DistrictKey,
    EventKey,
    MatchKey,
    TeamKey,
)
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.models.zebra_motionworks import ZebraMotionWorks
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
    def store_teams(data: List[Dict]) -> List[Team]:
        teams = [TeamConverter.dictToModel_v3(t) for t in data]
        if not teams:
            return []
        return listify(TeamManipulator.createOrUpdate(teams))

    @staticmethod
    def store_district_teams(
        teams: List[Team], district: District
    ) -> List[DistrictTeam]:
        district_teams = [
            DistrictTeam(
                id="{}_{}".format(district.key_name, team.key_name),
                district_key=district.key,
                team=team.key,
                year=district.year,
            )
            for team in teams
        ]
        if not district_teams:
            return []
        return listify(DistrictTeamManipulator.createOrUpdate(district_teams))

    @staticmethod
    def store_team_medias(
        data: List[Dict], year: Optional[int], team_key: Optional[TeamKey]
    ) -> List[Media]:
        medias = [MediaConverter.dictToModel_v3(m, year, team_key) for m in data]
        if not medias:
            return []
        return listify(MediaManipulator.createOrUpdate(medias))

    @classmethod
    def store_match(cls, data: Dict) -> Match:
        match = MatchConverter.dictToModel_v3(data)

        return MatchManipulator.createOrUpdate(match)

    @classmethod
    def store_matches(cls, data: List[Dict]) -> List[Match]:
        matches = [MatchConverter.dictToModel_v3(m) for m in data]
        if not matches:
            return []
        return listify(MatchManipulator.createOrUpdate(matches))

    @classmethod
    def store_match_zebra(cls, data: Dict) -> None:
        if data is None:
            return
        match_key = data["key"]
        event_key = match_key.split("_")[0]
        ZebraMotionWorks(id=match_key, event=ndb.Key(Event, event_key), data=data).put()

    @staticmethod
    def store_eventteams(
        teams: List[Team],
        event: Event,
        pit_locations: Optional[Dict[str, EventTeamPitLocation]] = None,
    ) -> List[EventTeam]:
        eventteams = []
        for team in teams:
            eventteam = EventTeam(id="{}_{}".format(event.key_name, team.key_name))
            eventteam.event = event.key
            eventteam.team = team.key
            eventteam.year = event.year
            if pit_locations and team.key_name in pit_locations:
                eventteam.pit_location = pit_locations[team.key_name]
            eventteams.append(eventteam)

        if not eventteams:
            return []
        return listify(EventTeamManipulator.createOrUpdate(eventteams))

    @classmethod
    def store_event_details(cls, event: Event, **attrs: Any) -> EventDetails:
        """
        Write all of the given EventDetails attrs (rankings2, alliance_selections,
        predictions, district_points, ...) in a single createOrUpdate call, instead
        of a separate get_or_insert + createOrUpdate round-trip per attr.
        """
        detail = EventDetails(id=event.key_name)
        for attr, value in attrs.items():
            setattr(detail, attr, value)

        return EventDetailsManipulator.createOrUpdate(detail)

    @classmethod
    def store_awards(cls, data: List[Dict], event: Event) -> List[Award]:
        awards = [AwardConverter.dictToModel_v3(a, event) for a in data]
        if not awards:
            return []
        return listify(AwardManipulator.createOrUpdate(awards))

    @classmethod
    def fetch_endpoint(cls, endpoint: str, auth_token: str) -> Union[Dict, List]:
        full_url = f"https://www.thebluealliance.com/api/v3/{endpoint}"
        r = requests.get(
            full_url, headers={cls.AUTH_HEADER: auth_token, "User-agent": "Mozilla/5.0"}
        )
        return r.json()

    @classmethod
    def fetch_team(cls, team_key: TeamKey, auth_token: str) -> Dict:
        return cast(Dict, cls.fetch_endpoint(f"team/{team_key}", auth_token))

    @classmethod
    def fetch_team_media(
        cls, team_key: TeamKey, year: int, auth_token: str
    ) -> List[Dict]:
        return cast(
            List[Dict], cls.fetch_endpoint(f"team/{team_key}/media/{year}", auth_token)
        )

    @classmethod
    def fetch_event(cls, event_key: EventKey, auth_token: str) -> Dict:
        return cast(Dict, cls.fetch_endpoint(f"event/{event_key}", auth_token))

    @classmethod
    def fetch_match(cls, match_key: MatchKey, auth_token: str) -> Dict:
        return cast(Dict, cls.fetch_endpoint(f"match/{match_key}", auth_token))

    @classmethod
    def fetch_district_history(
        cls, district_abbr: DistrictAbbreviation, auth_token: str
    ) -> Dict:
        return cast(
            Dict, cls.fetch_endpoint(f"district/{district_abbr}/history", auth_token)
        )

    @classmethod
    def fetch_district_events(cls, district_key: DistrictKey, auth_token: str) -> Dict:
        return cast(
            Dict, cls.fetch_endpoint(f"district/{district_key}/events", auth_token)
        )

    @classmethod
    def fetch_match_zebra(cls, match_key: MatchKey, auth_token: str) -> Dict:
        return cast(
            Dict, cls.fetch_endpoint(f"match/{match_key}/zebra_motionworks", auth_token)
        )

    @classmethod
    def fetch_district_rankings(
        cls, district_key: DistrictKey, auth_token: str
    ) -> List[Dict]:
        return cast(
            List[Dict],
            cls.fetch_endpoint(f"district/{district_key}/rankings", auth_token),
        )

    @classmethod
    def fetch_event_detail(
        cls, event_key: EventKey, detail: str, auth_token: str
    ) -> Dict:
        return cast(Dict, cls.fetch_endpoint(f"event/{event_key}/{detail}", auth_token))

    @classmethod
    def fetch_district_teams(
        cls, district_key: DistrictKey, auth_token: str
    ) -> List[Dict]:
        return cast(
            List[Dict], cls.fetch_endpoint(f"district/{district_key}/teams", auth_token)
        )

    @classmethod
    def update_events(cls, keys: List[EventKey], auth_token: str) -> None:
        for key in keys:
            cls.update_event(key, auth_token)

    @classmethod
    def _fetch_event_bundle(cls, key: EventKey, auth_token: str) -> Dict[str, Any]:
        """
        Fetch the event resource and all of its sub-resources concurrently, since
        none of these API calls depend on each other's results. This turns ~9
        sequential blocking HTTP round-trips per event into 1 round-trip's worth
        of wall-clock time.
        """
        fetchers: Dict[str, Callable[[], Union[Dict, List]]] = {
            "event": lambda: cls.fetch_event(key, auth_token),
            "teams": lambda: cls.fetch_event_detail(key, "teams", auth_token),
            "teams_statuses": lambda: cls.fetch_event_detail(
                key, "teams/statuses", auth_token
            ),
            "matches": lambda: cls.fetch_event_detail(key, "matches", auth_token),
            "rankings": lambda: cls.fetch_event_detail(key, "rankings", auth_token),
            "alliances": lambda: cls.fetch_event_detail(key, "alliances", auth_token),
            "awards": lambda: cls.fetch_event_detail(key, "awards", auth_token),
            "predictions": lambda: cls.fetch_event_detail(
                key, "predictions", auth_token
            ),
            "district_points": lambda: cls.fetch_event_detail(
                key, "district_points", auth_token
            ),
        }
        with ThreadPoolExecutor(max_workers=len(fetchers)) as executor:
            futures = {name: executor.submit(fn) for name, fn in fetchers.items()}
            return {name: future.result() for name, future in futures.items()}

    @classmethod
    def update_event(cls, key: EventKey, auth_token: str) -> None:
        fetched = cls._fetch_event_bundle(key, auth_token)

        event = cls.store_event(fetched["event"])

        teams = cls.store_teams(fetched["teams"])

        # Fold pit locations (from the teams/statuses endpoint) into the same
        # batch write as the EventTeams themselves, instead of a separate
        # get + put per team.
        pit_locations: Dict[str, EventTeamPitLocation] = {}
        event_statuses = fetched["teams_statuses"]
        if event_statuses:
            for team_key_str, status in event_statuses.items():
                if status and "pit_location" in status:
                    pit_locations[team_key_str] = EventTeamPitLocation(
                        location=status["pit_location"]
                    )
        cls.store_eventteams(teams, event, pit_locations)

        cls.store_matches(fetched["matches"])
        cls.store_awards(fetched["awards"], event)

        event_rankings = fetched["rankings"]
        detail_attrs: Dict[str, Any] = {
            "rankings2": event_rankings["rankings"] if event_rankings else [],
            "alliance_selections": fetched["alliances"],
            "predictions": fetched["predictions"],
        }
        event_district_points = fetched["district_points"]
        if event_district_points:
            detail_attrs["district_points"] = event_district_points
        cls.store_event_details(event, **detail_attrs)

    @classmethod
    def update_team(cls, key: TeamKey, auth_token: str) -> None:
        team_data = cls.fetch_team(key, auth_token)
        cls.store_team(team_data)

        year = datetime.now().year
        media_data = cls.fetch_team_media(key, year, auth_token)
        cls.store_team_medias(media_data, year, key)

    @classmethod
    def update_match(cls, key: MatchKey, auth_token: str) -> None:
        match_data = cls.fetch_match(key, auth_token)
        cls.store_match(match_data)

        zebra_data = cls.fetch_match_zebra(key, auth_token)
        cls.store_match_zebra(zebra_data)

    @classmethod
    def update_district(cls, district_data: Dict, auth_token: str) -> None:
        district = cls.store_district(district_data)

        district_teams_data = cls.fetch_district_teams(district.key_name, auth_token)
        teams = cls.store_teams(district_teams_data)
        cls.store_district_teams(teams, district)

        district_events = cls.fetch_district_events(district.key_name, auth_token)
        for event in district_events:
            defer_safe(cls.update_event, event["key"], auth_token)

        district.rankings = cast(
            List[DistrictRanking],
            cls.fetch_district_rankings(district.key_name, auth_token),
        )
        DistrictManipulator.createOrUpdate(district, update_manual_attrs=False)

    @classmethod
    def bootstrap_key(cls, key: str, apiv3_key: str) -> Optional[str]:
        if Match.validate_key_name(key):
            cls.update_match(key, apiv3_key)
            return f"/match/{key}"
        elif Event.validate_key_name(key):
            cls.update_event(key, apiv3_key)
            return f"/event/{key}"
        elif Team.validate_key_name(key):
            cls.update_team(key, apiv3_key)
            return f"/team/{key[3:]}"
        elif key.isdigit():
            event_keys = [
                event["key"] for event in cls.fetch_endpoint(f"events/{key}", apiv3_key)
            ]
            for event_key in event_keys:
                defer_safe(cls.update_event, event_key, apiv3_key)

            districts = cls.fetch_endpoint(f"districts/{key}", apiv3_key)
            for district_data in districts:
                defer_safe(cls.update_district, district_data, apiv3_key)

            return f"/events/{key}"
        elif key in ALL_KNOWN_DISTRICT_ABBREVIATIONS:
            # bootstrap all years for the given district abbr
            district_history = cls.fetch_district_history(key, apiv3_key)
            for district_year in district_history:
                defer_safe(cls.update_district, district_year, apiv3_key)

            return f"/events/{key}"
        else:
            return None
