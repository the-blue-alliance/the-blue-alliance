import json

from typing import Any, Dict, List, Optional, Set, Tuple

from google.appengine.ext import ndb

from backend.common.consts.media_type import MediaType
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.tasks_io.datafeeds.parsers.json.parser_paginated_json import (
    ParserPaginatedJSON,
)


class FMSAPITeamAvatarParser(ParserPaginatedJSON[Tuple[List[Media], Set[ndb.Key]]]):
    def __init__(self, year: int):
        self.year = year

    def parse(
        self, response: Dict[str, Any]
    ) -> Tuple[Optional[Tuple[List[Media], Set[ndb.Key]]], bool]:
        current_page = response["pageCurrent"]
        total_pages = response["pageTotal"]

        avatars: List[Media] = []
        media_keys_to_delete: Set[ndb.Key] = set()

        for teamData in response["teams"]:
            team_number = teamData["teamNumber"]
            foreign_key = "avatar_{}_frc{}".format(self.year, team_number)
            media_key = ndb.Key(
                Media, Media.render_key_name(MediaType.AVATAR, foreign_key)
            )

            encoded_avatar = teamData["encodedAvatar"]
            if not encoded_avatar:
                media_keys_to_delete.add(media_key)
                continue

            avatars.append(
                Media(
                    key=media_key,
                    details_json=json.dumps({"base64Image": encoded_avatar}),
                    foreign_key=foreign_key,
                    media_type_enum=MediaType.AVATAR,
                    references=[ndb.Key(Team, "frc{}".format(team_number))],
                    year=self.year,
                )
            )

        return (
            (
                (avatars, media_keys_to_delete)
                if avatars or media_keys_to_delete
                else None
            ),
            (current_page < total_pages),
        )
