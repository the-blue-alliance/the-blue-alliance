from freezegun import freeze_time
from werkzeug.test import Client

from backend.common.consts.media_type import MediaType
from backend.common.models.media import Media
from backend.common.models.team import Team


@freeze_time("2025-03-15")
def test_seed_team_redirects(local_client: Client, taskqueue_stub) -> None:
    resp = local_client.post("/local/seed_test_team")
    assert resp.status_code == 302
    assert "/team/2" in resp.headers["Location"]


@freeze_time("2025-03-15")
def test_seed_team_creates_team(local_client: Client, taskqueue_stub) -> None:
    local_client.post("/local/seed_test_team")

    team = Team.get_by_id("frc2")
    assert team is not None
    assert team.team_number == 2
    assert team.nickname == "The Reindeer"
    assert team.name == "North Pole High School & The Reindeer"
    assert team.city == "North Pole"
    assert team.state_prov == "AK"
    assert team.country == "USA"
    assert team.school_name == "North Pole High School"
    assert team.website == "https://www.thebluealliance.com/team/2"
    assert team.rookie_year == 1997
    assert team.motto == "Dasher, Dancer, Prancer, Vixen!"


@freeze_time("2025-03-15")
def test_seed_team_creates_media(local_client: Client, taskqueue_stub) -> None:
    local_client.post("/local/seed_test_team")

    team_ref = Media.create_reference("team", "frc2")

    # YouTube video
    yt_video = Media.get_by_id(
        Media.render_key_name(MediaType.YOUTUBE_VIDEO, "dQw4w9WgXcQ")
    )
    assert yt_video is not None
    assert yt_video.media_type_enum == MediaType.YOUTUBE_VIDEO
    assert yt_video.foreign_key == "dQw4w9WgXcQ"
    assert yt_video.year == 2025
    assert team_ref in yt_video.references

    # Imgur image
    imgur = Media.get_by_id(Media.render_key_name(MediaType.IMGUR, "aF8T5ZE"))
    assert imgur is not None
    assert imgur.media_type_enum == MediaType.IMGUR
    assert imgur.foreign_key == "aF8T5ZE"
    assert team_ref in imgur.references

    # Instagram image
    ig_image = Media.get_by_id(
        Media.render_key_name(MediaType.INSTAGRAM_IMAGE, "B9ZUsERhIWi")
    )
    assert ig_image is not None
    assert ig_image.media_type_enum == MediaType.INSTAGRAM_IMAGE
    assert ig_image.foreign_key == "B9ZUsERhIWi"
    assert team_ref in ig_image.references

    # YouTube channel
    yt_channel = Media.get_by_id(
        Media.render_key_name(MediaType.YOUTUBE_CHANNEL, "bobcatrobotics")
    )
    assert yt_channel is not None
    assert yt_channel.media_type_enum == MediaType.YOUTUBE_CHANNEL
    assert yt_channel.foreign_key == "bobcatrobotics"
    assert team_ref in yt_channel.references

    # Instagram profile
    ig_profile = Media.get_by_id(
        Media.render_key_name(MediaType.INSTAGRAM_PROFILE, "bobcatrobotics")
    )
    assert ig_profile is not None
    assert ig_profile.media_type_enum == MediaType.INSTAGRAM_PROFILE
    assert ig_profile.foreign_key == "bobcatrobotics"
    assert team_ref in ig_profile.references
