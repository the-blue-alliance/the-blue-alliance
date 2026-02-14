import json

from typing import List, Optional, Set, Tuple

from google.appengine.ext import ndb

from backend.common.consts.media_type import MediaType
from backend.common.frc_api.types import TeamAvatarListingsModelV2, TeamAvatarModelV2
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.tasks_io.datafeeds.parsers.parser_paginated import (
    ParserPaginated,
)


class FMSAPITeamAvatarParser(
    ParserPaginated[TeamAvatarListingsModelV2, Tuple[List[Media], Set[ndb.Key]]]
):
    def __init__(self, year: int):
        self.year = year

    def parse(
        self, response: TeamAvatarListingsModelV2
    ) -> Tuple[Optional[Tuple[List[Media], Set[ndb.Key]]], bool]:
        current_page = response["pageCurrent"]
        total_pages = response["pageTotal"]

        avatars: List[Media] = []
        media_keys_to_delete: Set[ndb.Key] = set()

        api_avatars: list[TeamAvatarModelV2] = response["teams"] or []
        for teamData in api_avatars:
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
