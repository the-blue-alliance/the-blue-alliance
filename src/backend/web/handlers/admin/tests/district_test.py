from unittest.mock import patch

import bs4
from freezegun import freeze_time
from google.appengine.ext import ndb
from werkzeug.test import Client

from backend.common.consts.webcast_type import WebcastType
from backend.common.futures import InstantFuture
from backend.common.helpers.youtube_video_helper import (
    YouTubeChannel,
    YouTubeVideoHelper,
)
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.webcast import WebcastChannel
from backend.web.handlers.tests import helpers


@freeze_time("2021-04-01")
def test_district_list_current_year(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/districts")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    assert soup.find("title").contents == ["District List (2021) - TBA Admin"]


def test_district_list(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.get("/admin/districts/2020")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    assert soup.find("title").contents == ["District List (2020) - TBA Admin"]


def test_district_list_none_for_year(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.get("/admin/districts/2021")
    assert resp.status_code == 200


def test_district_list_shows_fetch_upcoming_webcasts_button_when_configured(
    web_client: Client, login_gae_admin
) -> None:
    helpers.preseed_district("2020ne")
    district = District.get_by_id("2020ne")
    assert district is not None
    district.webcast_channels = [
        WebcastChannel(
            type=WebcastType.YOUTUBE,
            channel="NE FIRST",
            channel_id="UC123",
        )
    ]
    district.put()

    resp = web_client.get("/admin/districts/2020")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    assert soup.find("a", href="/tasks/do/find_event_webcasts/2020ne") is not None


def test_district_list_hides_fetch_upcoming_webcasts_button_when_not_configured(
    web_client: Client, login_gae_admin
) -> None:
    helpers.preseed_district("2020ne")

    resp = web_client.get("/admin/districts/2020")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    assert soup.find("a", href="/tasks/do/find_event_webcasts/2020ne") is None


def test_district_details_webcasts_tab_shows_configured_channels(
    web_client: Client, login_gae_admin
) -> None:
    helpers.preseed_district("2020ne")
    district = District.get_by_id("2020ne")
    assert district is not None
    district.webcast_channels = [
        WebcastChannel(
            type=WebcastType.YOUTUBE,
            channel="NE FIRST",
            channel_id="UC123",
        )
    ]
    district.put()

    resp = web_client.get("/admin/district/2020ne")
    assert resp.status_code == 200
    assert b"Webcasts" in resp.data
    assert b"NE FIRST" in resp.data
    assert b"UC123" in resp.data
    assert b'href="https://www.youtube.com/channel/UC123"' in resp.data
    assert b'target="_blank"' in resp.data


def test_district_details_shows_fetch_upcoming_webcasts_button_when_configured(
    web_client: Client, login_gae_admin
) -> None:
    helpers.preseed_district("2020ne")
    district = District.get_by_id("2020ne")
    assert district is not None
    district.webcast_channels = [
        WebcastChannel(
            type=WebcastType.YOUTUBE,
            channel="NE FIRST",
            channel_id="UC123",
        )
    ]
    district.put()

    resp = web_client.get("/admin/district/2020ne")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    assert soup.find("a", href="/tasks/do/find_event_webcasts/2020ne") is not None


def test_district_details_hides_fetch_upcoming_webcasts_button_when_not_configured(
    web_client: Client, login_gae_admin
) -> None:
    helpers.preseed_district("2020ne")

    resp = web_client.get("/admin/district/2020ne")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    assert soup.find("a", href="/tasks/do/find_event_webcasts/2020ne") is None


def test_district_add_webcast_channel_post(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    helpers.preseed_district("2020ne")

    with patch.object(
        YouTubeVideoHelper,
        "resolve_channel_id",
        return_value=InstantFuture(
            YouTubeChannel(
                channel_id="UCjX4WSaAFPgM2PYr-6P",
                channel_name="FIRST in Michigan",
            )
        ),
    ):
        resp = web_client.post(
            "/admin/district/2020ne/webcasts/add",
            data={"channel_name": "FIRST in Michigan"},
        )

    assert resp.status_code == 302
    assert (
        resp.headers["Location"]
        == "/admin/district/2020ne?webcast_success=channel_added#webcasts"
    )

    district = District.get_by_id("2020ne")
    assert district is not None
    assert district.webcast_channels == [
        WebcastChannel(
            type=WebcastType.YOUTUBE,
            channel="FIRST in Michigan",
            channel_id="UCjX4WSaAFPgM2PYr-6P",
        )
    ]


def test_district_add_webcast_channel_post_channel_not_found(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    helpers.preseed_district("2020ne")

    with patch.object(
        YouTubeVideoHelper,
        "resolve_channel_id",
        return_value=InstantFuture(None),
    ):
        resp = web_client.post(
            "/admin/district/2020ne/webcasts/add",
            data={"channel_name": "Unknown Channel"},
        )

    assert resp.status_code == 302
    assert (
        resp.headers["Location"]
        == "/admin/district/2020ne?webcast_error=channel_not_found#webcasts"
    )

    district = District.get_by_id("2020ne")
    assert district is not None
    assert district.webcast_channels == []


def test_district_remove_webcast_channel_post(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    helpers.preseed_district(
        "2020ne",
        webcast_channels=[
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="FIRST in Michigan",
                channel_id="UCjX4WSaAFPgM2PYr-6P",
            ),
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="Another Channel",
                channel_id="UC_another",
            ),
        ],
    )

    resp = web_client.post(
        "/admin/district/2020ne/webcasts/remove",
        data={"channel_id": "UCjX4WSaAFPgM2PYr-6P"},
    )

    assert resp.status_code == 302
    assert (
        resp.headers["Location"]
        == "/admin/district/2020ne?webcast_success=channel_removed#webcasts"
    )

    district = District.get_by_id("2020ne")
    assert district is not None
    assert len(district.webcast_channels) == 1
    assert district.webcast_channels[0]["channel"] == "Another Channel"
    assert district.webcast_channels[0]["channel_id"] == "UC_another"


def test_district_remove_webcast_channel_post_channel_not_found(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    helpers.preseed_district(
        "2020ne",
        webcast_channels=[
            WebcastChannel(
                type=WebcastType.YOUTUBE,
                channel="FIRST in Michigan",
                channel_id="UCjX4WSaAFPgM2PYr-6P",
            )
        ],
    )

    resp = web_client.post(
        "/admin/district/2020ne/webcasts/remove",
        data={"channel_id": "UC_nonexistent"},
    )

    assert resp.status_code == 302
    assert (
        resp.headers["Location"]
        == "/admin/district/2020ne?webcast_error=channel_not_found_to_remove#webcasts"
    )

    district = District.get_by_id("2020ne")
    assert district is not None
    assert len(district.webcast_channels) == 1


def test_district_edit_bad_event(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/district/edit/2021asdf")
    assert resp.status_code == 404


def test_district_edit(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.get("/admin/district/edit/2020ne")
    assert resp.status_code == 200


def test_edit_district(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.post(
        "/admin/district/edit/2020ne",
        data={
            "year": "2020",
            "abbreviation": "ne",
            "display_name": "New England",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/districts/2020"

    district = District.get_by_id("2020ne")
    assert district is not None
    assert district.display_name == "New England"


def test_district_create(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/district/create")
    assert resp.status_code == 200


def test_create_district(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/district/edit",
        data={
            "year": "2021",
            "abbreviation": "ne",
            "display_name": "New England",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/districts/2021"

    district = District.get_by_id("2021ne")
    assert district is not None
    assert district.display_name == "New England"


def test_create_district_invalid_key(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/district/edit",
        data={
            "year": "2020",
            "abbreviation": "ne_",
            "display_name": "New England",
        },
    )
    assert resp.status_code == 400

    assert District.query().count() == 0


def test_district_delete(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.get("/admin/district/delete/2020ne")
    assert resp.status_code == 200


def test_district_delete_bad_key(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/district/delete/2020asdf")
    assert resp.status_code == 404


def test_delete_district(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    helpers.preseed_district("2020ne")
    resp = web_client.post("/admin/district/delete/2020ne")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/districts/2020"

    district = District.get_by_id("2020ne")
    assert district is None

    district_teams = DistrictTeam.query(
        DistrictTeam.district_key == ndb.Key(District, "2020ne")
    ).fetch()
    assert district_teams == []


def test_delete_district_bad_key(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post("/admin/district/delete/2020ne")
    assert resp.status_code == 404
