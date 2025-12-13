import json

from google.appengine.ext import ndb

from backend.common.consts.media_type import MediaType
from backend.common.models.media import Media
from backend.common.models.team import Team
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_team_avatar_parser import (
    FMSAPITeamAvatarParser,
)


def test_parse_avatars_none(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2021_avatars_none.json")
    with open(path, "r") as f:
        data = json.load(f)

    avatars, more_results = FMSAPITeamAvatarParser(2021).parse(data)

    assert avatars is None
    assert more_results is False


def test_parse_avatars_only_media(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2021_avatars_only_media.json")
    with open(path, "r") as f:
        data = json.load(f)

    avatars_tuple, more_results = FMSAPITeamAvatarParser(2021).parse(data)

    assert avatars_tuple is not None
    assert more_results is False

    avatars, media_keys_to_delete = avatars_tuple
    assert len(avatars) == 1
    assert len(media_keys_to_delete) == 0


def test_parse_avatars_only_delete(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2021_avatars_only_delete.json")
    with open(path, "r") as f:
        data = json.load(f)

    avatars_tuple, more_results = FMSAPITeamAvatarParser(2021).parse(data)

    assert avatars_tuple is not None
    assert more_results is False

    avatars, media_keys_to_delete = avatars_tuple
    assert len(avatars) == 0
    assert len(media_keys_to_delete) == 1


def test_parse_avatars(test_data_importer, ndb_stub):
    path = test_data_importer._get_path(__file__, "data/2021_avatars.json")
    with open(path, "r") as f:
        data = json.load(f)

    avatars_tuple, more_results = FMSAPITeamAvatarParser(2021).parse(data)

    assert avatars_tuple is not None
    assert more_results is True

    avatars, media_keys_to_delete = avatars_tuple

    assert len(avatars) == 6
    first_media = avatars[0]
    assert first_media.key == ndb.Key(Media, "avatar_avatar_2021_frc226")
    first_media_details = json.loads(first_media.details_json)
    assert first_media_details["base64Image"] is not None
    assert first_media.foreign_key == "avatar_2021_frc226"
    assert first_media.media_type_enum == MediaType.AVATAR
    assert first_media.references == [ndb.Key(Team, "frc226")]
    assert first_media.year == 2021

    # Spot check delete keys
    assert len(media_keys_to_delete) == 59
    first_delete = next(
        iter(
            [
                m
                for m in media_keys_to_delete
                if m.string_id() == "avatar_avatar_2021_frc1"
            ]
        ),
        None,
    )
    assert first_delete == ndb.Key(Media, "avatar_avatar_2021_frc1")
