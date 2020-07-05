import json
import os
from contextlib import contextmanager
from typing import Generator, List, Optional

from google.cloud import ndb

from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import TeamKey
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

    ndb_client: ndb.Client

    def __init__(self, ndb_client: ndb.Client) -> None:
        self.ndb_client = ndb_client

    @staticmethod
    def _get_path(base_path: str, path: str) -> str:
        base_dir = os.path.dirname(base_path)
        return os.path.join(base_dir, f"{path}")

    @contextmanager
    def _maybe_with_context(self) -> Generator[ndb.Context, None, None]:
        context = ndb.context.get_context(raise_context_error=False)
        if context:
            yield context
            return
        with self.ndb_client.context() as c:
            yield c  # pyre-ignore

    def import_team(self, base_path: str, path: str) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        with self._maybe_with_context():
            team = TeamConverter.dictToModel_v3(data)
            team.put()

    def import_event_list(self, base_path: str, path: str, team_key: TeamKey) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        with self._maybe_with_context():
            [EventConverter.dictToModel_v3(e).put() for e in data]
            [
                EventTeam(
                    id=f"{e['key']}_{team_key}",
                    event=ndb.Key(Event, e["key"]),
                    team=ndb.Key(Team, team_key),
                    year=e["year"],
                ).put()
                for e in data
            ]

    def import_match(self, base_path: str, path: str) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        with self._maybe_with_context():
            match = MatchConverter.dictToModel_v3(data)
            match.put()

    def import_match_list(self, base_path: str, path: str) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        with self._maybe_with_context():
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

        with self._maybe_with_context():
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

        with self._maybe_with_context():
            [MediaConverter.dictToModel_v3(m, year, team_key).put() for m in data]

    def import_award_list(self, base_path: str, path: str) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        with self._maybe_with_context():
            [
                AwardConverter.dictToModel_v3(a, Event.get_by_id(a["event_key"])).put()
                for a in data
            ]

    def import_district_list(
        self, base_path: str, path: str, team_key: TeamKey
    ) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        with self._maybe_with_context():
            [DistrictConverter.dictToModel_v3(d).put() for d in data]
            [
                DistrictTeam(
                    id=DistrictTeam.renderKeyName(d["key"], team_key),
                    team=ndb.Key(Team, team_key),
                    district_key=ndb.Key(District, d["key"]),
                    year=d["year"],
                ).put()
                for d in data
            ]

    def import_robot_list(self, base_path: str, path: str) -> None:
        with open(self._get_path(base_path, path), "r") as f:
            data = json.load(f)

        with self._maybe_with_context():
            [RobotConverter.dictToModel_v3(d).put() for d in data]
