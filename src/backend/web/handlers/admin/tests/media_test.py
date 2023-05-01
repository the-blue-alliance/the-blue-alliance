from pyre_extensions import none_throws
from werkzeug.test import Client

from backend.common.models.media import Media
from backend.common.suggestions.media_parser import MediaParser


def test_media_dashboard(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/media")
    assert resp.status_code == 200


def test_delete_reference_no_media(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/media/delete_reference/asdf",
        data={
            "reference_type": "team",
            "reference_key_name": "frc1124",
            "originating_url": "/admin/team/1124",
        },
    )
    assert resp.status_code == 404


def test_delete_reference(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    media_reference = Media.create_reference("team", "frc1124")
    media_dict = none_throws(
        MediaParser.partial_media_dict_from_url("http://imgur.com/aF8T5ZE")
    )
    media = Media(
        id=Media.render_key_name(
            media_dict["media_type_enum"], media_dict["foreign_key"]
        ),
        foreign_key=media_dict["foreign_key"],
        media_type_enum=media_dict["media_type_enum"],
        details_json=media_dict.get("details_json", None),
        year=2010,
        references=[media_reference],
    )
    media.put()

    resp = web_client.post(
        f"/admin/media/delete_reference/{media.key_name}",
        data={
            "reference_type": "team",
            "reference_key_name": "frc1124",
            "originating_url": "/admin/team/1124",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/team/1124"

    media = Media.get_by_id(media.key_name)
    assert media is not None
    assert media.references == []
    assert media.preferred_references == []


def test_make_preferred_no_media(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/media/make_preferred/asdf",
        data={
            "reference_type": "team",
            "reference_key_name": "frc1124",
            "originating_url": "/admin/team/1124",
        },
    )
    assert resp.status_code == 404


def test_make_preferred(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    media_reference = Media.create_reference("team", "frc1124")
    media_dict = none_throws(
        MediaParser.partial_media_dict_from_url("http://imgur.com/aF8T5ZE")
    )
    media = Media(
        id=Media.render_key_name(
            media_dict["media_type_enum"], media_dict["foreign_key"]
        ),
        foreign_key=media_dict["foreign_key"],
        media_type_enum=media_dict["media_type_enum"],
        details_json=media_dict.get("details_json", None),
        year=2010,
        references=[media_reference],
    )
    media.put()

    resp = web_client.post(
        f"/admin/media/make_preferred/{media.key_name}",
        data={
            "reference_type": "team",
            "reference_key_name": "frc1124",
            "originating_url": "/admin/team/1124",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/team/1124"

    media = Media.get_by_id(media.key_name)
    assert media is not None
    assert media.references == [media_reference]
    assert media.preferred_references == [media_reference]


def test_remove_preferred_no_media(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/media/remove_preferred/asdf",
        data={
            "reference_type": "team",
            "reference_key_name": "frc1124",
            "originating_url": "/admin/team/1124",
        },
    )
    assert resp.status_code == 404


def test_remove_preferred(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    media_reference = Media.create_reference("team", "frc1124")
    media_dict = none_throws(
        MediaParser.partial_media_dict_from_url("http://imgur.com/aF8T5ZE")
    )
    media = Media(
        id=Media.render_key_name(
            media_dict["media_type_enum"], media_dict["foreign_key"]
        ),
        foreign_key=media_dict["foreign_key"],
        media_type_enum=media_dict["media_type_enum"],
        details_json=media_dict.get("details_json", None),
        year=2010,
        references=[media_reference],
        preferred_references=[media_reference],
    )
    media.put()

    resp = web_client.post(
        f"/admin/media/remove_preferred/{media.key_name}",
        data={
            "reference_type": "team",
            "reference_key_name": "frc1124",
            "originating_url": "/admin/team/1124",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/team/1124"

    media = Media.get_by_id(media.key_name)
    assert media is not None
    assert media.references == [media_reference]
    assert media.preferred_references == []


def test_media_add_bad_url(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/media/add_media",
        data={
            "media_url": "https://aslkhfasld",
            "year": "2010",
            "reference_type": "team",
            "reference_key": "frc1124",
            "originating_url": "/admin/team/1124",
        },
    )
    assert resp.status_code == 400

    media_reference = Media.create_reference("team", "frc1124")
    media_query = Media.query(Media.references == media_reference)
    assert media_query.count() == 0


def test_media_add_with_year(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/media/add_media",
        data={
            "media_url": "http://imgur.com/aF8T5ZE",
            "year": "2010",
            "reference_type": "team",
            "reference_key": "frc1124",
            "originating_url": "/admin/team/1124",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/team/1124"

    media_reference = Media.create_reference("team", "frc1124")
    medias = Media.query(Media.references == media_reference).fetch()
    assert len(medias) == 1

    media = medias[0]
    assert media.year == 2010
    assert media.references == [media_reference]


def test_media_add_without_year(
    web_client: Client, login_gae_admin, ndb_stub, taskqueue_stub
) -> None:
    resp = web_client.post(
        "/admin/media/add_media",
        data={
            "media_url": "http://imgur.com/aF8T5ZE",
            "year": "",
            "reference_type": "team",
            "reference_key": "frc1124",
            "originating_url": "/admin/team/1124",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/team/1124"

    media_reference = Media.create_reference("team", "frc1124")
    medias = Media.query(Media.references == media_reference).fetch()
    assert len(medias) == 1

    media = medias[0]
    assert media.year is None
    assert media.references == [media_reference]
