from unittest.mock import patch

from werkzeug.test import Client

from backend.common.consts.media_tag import MediaTag
from backend.common.consts.media_type import MediaType
from backend.common.models.media import Media
from backend.tasks_io.datafeeds.parsers.first.resource_library_parser import (
    ParsedHallOfFameTeam,
)

PARSED_TEAMS = [
    ParsedHallOfFameTeam(
        team_id="frc2486",
        team_number=2486,
        year=2024,
        video="9oBL8s2Y7tA",
        presentation="TIFLhevHf7k",
        essay="https://www.firstinspires.org/essays/2024/2486.pdf",
    ),
    ParsedHallOfFameTeam(
        team_id="frc1629",
        team_number=1629,
        year=2022,
        video=None,
        presentation=None,
        essay="https://www.firstinspires.org/essays/2022/1629.pdf",
    ),
]


def test_get_hof_teams(tasks_client: Client, ndb_stub) -> None:
    with patch(
        "backend.tasks_io.handlers.hall_of_fame.DatafeedResourceLibrary.get_hall_of_fame_teams",
        return_value=PARSED_TEAMS,
    ):
        resp = tasks_client.get("/tasks/get/hof_teams")

    assert resp.status_code == 200

    video = Media.get_by_id(
        Media.render_key_name(MediaType.YOUTUBE_VIDEO, "9oBL8s2Y7tA")
    )
    assert video is not None
    assert video.media_tag_enum == [MediaTag.CHAIRMANS_VIDEO]
    assert video.year == 2024

    presentation = Media.get_by_id(
        Media.render_key_name(MediaType.YOUTUBE_VIDEO, "TIFLhevHf7k")
    )
    assert presentation is not None
    assert presentation.media_tag_enum == [MediaTag.CHAIRMANS_PRESENTATION]
    assert presentation.year == 2024
    assert presentation.references == [Media.create_reference("team", "frc2486")]

    essay = Media.get_by_id(
        Media.render_key_name(
            MediaType.EXTERNAL_LINK,
            "https://www.firstinspires.org/essays/2024/2486.pdf",
        )
    )
    assert essay is not None
    assert essay.media_tag_enum == [MediaTag.CHAIRMANS_ESSAY]

    all_media = Media.query().fetch()
    assert len(all_media) == 4


def test_get_hof_teams_no_data(tasks_client: Client, ndb_stub) -> None:
    with patch(
        "backend.tasks_io.handlers.hall_of_fame.DatafeedResourceLibrary.get_hall_of_fame_teams",
        return_value=[],
    ):
        resp = tasks_client.get("/tasks/get/hof_teams")

    assert resp.status_code == 200
    assert Media.query().fetch() == []
