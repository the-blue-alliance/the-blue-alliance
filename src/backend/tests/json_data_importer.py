import json
import os
from typing import List, Optional

from google.appengine.ext import ndb
from pyre_extensions.refinement import none_throws

from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, TeamKey
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.common.queries.dict_converters.award_converter import AwardConverter
from backend.common.queries.dict_converters.district_converter import DistrictConverter
from backend.common.queries.dict_converters.event_converter import EventConverter
from backend.common.queries.dict_converters.match_converter import MatchConverter
from backend.common.queries.dict_converters.media_converter import MediaConverter
from backend.common.queries.dict_converters.robot_converter import RobotConverter
from backend.common.queries.dict_converters.team_converter import TeamConverter


class JsonDataImporter(object):
    @staticmethod
    def _get_path(base_path: str, path: str) -> str:
        base_dir = os.path.dirname(base_path)
        return os.path.join(base_dir, f"{path}")

    def import_team(self, base_path: str, path: str) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        team = TeamConverter.dictToModel_v3(data)
        team.put()

    def import_event_list(
        self, base_path: str, path: str, team_key: Optional[TeamKey] = None
    ) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        [EventConverter.dictToModel_v3(e).put() for e in data]
        if team_key:
            [
                EventTeam(
                    id=f"{e['key']}_{team_key}",
                    event=ndb.Key(Event, e["key"]),
                    team=ndb.Key(Team, team_key),
                    year=e["year"],
                ).put()
                for e in data
            ]

    def import_event(self, base_path: str, path: str) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        event = EventConverter.dictToModel_v3(data)
        event.put()

    def import_event_alliances(
        self, base_path: str, path: str, event_key: EventKey
    ) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        detail = EventDetails.get_or_insert(event_key)
        detail.alliance_selections = data
        detail.put()

    def import_event_predictions(
        self, base_path: str, path: str, event_key: EventKey
    ) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        detail = EventDetails.get_or_insert(event_key)
        detail.predictions = data
        detail.put()

    def import_event_district_points(
        self, base_path: str, path: str, event_key: EventKey
    ) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        detail = EventDetails.get_or_insert(event_key)
        detail.district_points = data
        detail.put()

    def maybe_import_event_regional_champs_pool_points(
        self, base_path: str, path: str, event_key: EventKey
    ) -> None:
        path = self._get_path(base_path, path)
        if not os.path.exists(path):
            return

        with open(path, "r") as f:
            data = json.load(f)

        detail = EventDetails.get_or_insert(event_key)
        detail.regional_champs_pool_points = data
        detail.put()

    def import_event_rankings(
        self, base_path: str, path: str, event_key: EventKey
    ) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        detail = EventDetails.get_or_insert(event_key)
        detail.rankings2 = data["rankings"]
        detail.put()

    def import_event_playoff_advancement(
        self, base_path: str, path: str, event_key: EventKey
    ) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        detail = EventDetails.get_or_insert(event_key)
        detail.playoff_advancement = data
        detail.put()

    def import_event_teams(
        self, base_path: str, path: str, event_key: EventKey
    ) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        teams = [TeamConverter.dictToModel_v3(t) for t in data]
        event_teams = [
            EventTeam(
                id=f"{event_key}_{team.key_name}",
                event=ndb.Key(Event, event_key),
                team=ndb.Key(Team, team.key_name),
                year=int(event_key[:4]),
            )
            for team in teams
        ]

        ndb.put_multi(teams)
        ndb.put_multi(event_teams)

    def import_match(self, base_path: str, path: str) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        match = MatchConverter.dictToModel_v3(data)
        match.put()

    def import_match_list(self, base_path: str, path: str) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        [MatchConverter.dictToModel_v3(m).put() for m in data]

    def parse_match_list(self, base_path: str, path: str) -> List[Match]:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        matches = [MatchConverter.dictToModel_v3(m) for m in data]
        return matches

    def parse_media_list(
        self,
        base_path: str,
        path: str,
        year: Optional[int] = None,
        team_key: Optional[TeamKey] = None,
    ) -> List[Media]:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        medias = [MediaConverter.dictToModel_v3(m, year, team_key) for m in data]
        return medias

    def import_media_list(
        self,
        base_path: str,
        path: str,
        year: Optional[int] = None,
        team_key: Optional[TeamKey] = None,
    ) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        [MediaConverter.dictToModel_v3(m, year, team_key).put() for m in data]

    def import_award_list(self, base_path: str, path: str) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        [
            AwardConverter.dictToModel_v3(
                a, none_throws(Event.get_by_id(a["event_key"]))
            ).put()
            for a in data
        ]

    def import_district_list(
        self, base_path: str, path: str, team_key: TeamKey
    ) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        [DistrictConverter.dictToModel_v3(d).put() for d in data]
        [
            DistrictTeam(
                id=DistrictTeam.render_key_name(d["key"], team_key),
                team=ndb.Key(Team, team_key),
                district_key=ndb.Key(District, d["key"]),
                year=d["year"],
            ).put()
            for d in data
        ]

    def import_robot_list(self, base_path: str, path: str) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        [RobotConverter.dictToModel_v3(d).put() for d in data]
