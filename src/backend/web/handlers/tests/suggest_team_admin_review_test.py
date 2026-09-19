import datetime
import json
import unittest
from typing import Optional
from urllib.parse import urlparse

import pytest
from flask.testing import FlaskClient
from google.appengine.ext import ndb

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.media_type import MediaType
from backend.common.consts.suggestion_state import SuggestionState
from backend.common.models.audit_log_entry import AuditLogEntry
from backend.common.models.media import Media
from backend.common.models.robot import Robot
from backend.common.models.suggestion import Suggestion
from backend.common.models.suggestion_dict import SuggestionDict
from backend.common.models.team import Team
from backend.common.models.team_admin_access import TeamAdminAccess
from backend.common.models.user import User
from backend.common.suggestions.media_creator import MediaCreator
from backend.common.suggestions.media_parser import MediaParser
from backend.common.suggestions.suggestion_creator import SuggestionCreator


def test_login_redirect(web_client):
    resp = web_client.get("/mod")

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/account/login"


def test_review_login_redirect(web_client):
    resp = web_client.post("/mod/review", data={})

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/account/login"


def test_review_get_not_allowed(login_user, web_client):
    resp = web_client.get("/mod/review")

    assert resp.status_code == 405


def test_mod_admin_can_view_with_forced_team_year(login_admin, web_client):
    Team(
        id="frc1124",
        team_number=1124,
    ).put()
    login_admin.has_permission.return_value = False

    resp = web_client.get(f"/mod?team=1124&year={datetime.datetime.now().year}")

    assert resp.status_code == 200


def test_mod_review_permission_can_view_with_forced_team_year(login_user, web_client):
    Team(
        id="frc1124",
        team_number=1124,
    ).put()
    login_user.has_permission.return_value = True
    login_user.permissions = [AccountPermission.REVIEW_MEDIA]

    resp = web_client.get(f"/mod?team=1124&year={datetime.datetime.now().year}")

    assert resp.status_code == 200
    assert b"Jump to Year" in resp.data
    assert b'name="team" value="1124"' in resp.data
    assert b'name="year"' in resp.data


def test_mod_without_review_permission_hides_year_jump(login_user, web_client):
    Team(
        id="frc1124",
        team_number=1124,
    ).put()
    TeamAdminAccess(
        id=TeamAdminAccess.render_key_name(1124, datetime.datetime.now().year),
        account=login_user.account_key,
        team_number=1124,
        year=datetime.datetime.now().year,
        expiration=datetime.datetime.now() + datetime.timedelta(days=1),
    ).put()

    resp = web_client.get("/mod")

    assert resp.status_code == 200
    assert b"Jump to Year" not in resp.data


def test_mod_post_admin_can_set_team_info(login_admin, web_client):
    Team(
        id="frc1124",
        team_number=1124,
    ).put()
    login_admin.has_permission.return_value = False

    resp = web_client.post(
        "/mod",
        data={
            "team_number": 1124,
            "action": "set_team_info",
            "robot_name": "",
        },
    )

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/mod"

    entries = AuditLogEntry.query().fetch()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.account == login_admin.account_key
    assert entry.endpoint == "team_admin.team_mod_post"
    assert entry.target_key is not None
    assert entry.target_key.kind() == "Team"
    assert entry.target_key.id() == "frc1124"
    assert entry.url_args == {}
    assert entry.form_params == {
        "team_number": ["1124"],
        "action": ["set_team_info"],
        "robot_name": [""],
    }


def test_mod_post_review_permission_can_set_team_info(login_user, web_client):
    Team(
        id="frc1124",
        team_number=1124,
    ).put()
    login_user.has_permission.return_value = True
    login_user.permissions = [AccountPermission.REVIEW_MEDIA]

    resp = web_client.post(
        "/mod",
        data={
            "team_number": 1124,
            "action": "set_team_info",
            "robot_name": "",
        },
    )

    assert resp.status_code == 302
    assert urlparse(resp.headers["Location"]).path == "/mod"


@pytest.fixture(autouse=True)
def mock_grabcad_api(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.common.futures import InstantFuture

    def mock_grabcad_dict(url: str) -> InstantFuture[SuggestionDict]:
        return InstantFuture(
            SuggestionDict(
                media_type_enum=MediaType.GRABCAD,
                foreign_key="2016-148-robowranglers-1",
                year=2016,
                details_json=json.dumps(
                    {
                        "model_name": "2016 | 148 - Robowranglers",
                        "model_description": "Renegade",
                        "model_image": "https://d2t1xqejof9utc.cloudfront.net/screenshots/pics/bf832651cc688c27a78c224fbd07d9d7/card.jpg",
                        "model_created": "2016-09-19T11:52:23Z",
                    }
                ),
            )
        )

    monkeypatch.setattr(
        MediaParser, "_partial_media_dict_from_grabcad", mock_grabcad_dict
    )


@pytest.mark.usefixtures(
    "web_client", "ndb_context", "taskqueue_stub", "login_user", "mock_grabcad_api"
)
class TestSuggestTeamAdminReview(unittest.TestCase):
    account: Optional[User] = None
    web_client: Optional[FlaskClient] = None
    team: Optional[Team] = None
    now: Optional[datetime.datetime] = None

    @pytest.fixture(autouse=True)
    def set_up(self, login_user: User, web_client):
        self.account = login_user
        self.web_client = web_client
        self.now = datetime.datetime.now()
        self.account.has_permission.return_value = False

        self.team = Team(
            id="frc1124",
            team_number=1124,
        )
        self.team.put()

    def giveTeamAdminAccess(self, expiration_days=1):
        access = TeamAdminAccess(
            id="test_access",
            team_number=1124,
            year=self.now.year,
            expiration=self.now + datetime.timedelta(days=expiration_days),
            account=self.account.account_key,
        )
        return access.put()

    def createMediaSuggestion(self):
        status = SuggestionCreator.createTeamMediaSuggestion(
            self.account.account_key,
            "http://imgur.com/foobar",
            "frc1124",
            str(self.now.year),
        ).get_result()
        self.assertEqual(status[0], "success")
        return Suggestion.query().fetch(keys_only=True)[0].id()

    def createSocialMediaSuggestion(self):
        status = SuggestionCreator.createTeamMediaSuggestion(
            self.account.account_key,
            "http://twitter.com/frc1124",
            "frc1124",
            None,
            None,
            True,
        ).get_result()
        self.assertEqual(status[0], "success")
        return Suggestion.query().fetch(keys_only=True)[0].id()

    def createDesignSuggestion(self):
        status = SuggestionCreator.createTeamMediaSuggestion(
            self.account.account_key,
            "https://grabcad.com/library/2016-148-robowranglers-1",
            "frc1124",
            "2016",
        ).get_result()
        self.assertEqual(status[0], "success")
        return Suggestion.render_media_key_name(
            2016, "team", "frc1124", "grabcad", "2016-148-robowranglers-1"
        )

    def test_no_access(self):
        resp = self.web_client.get("/mod")

        assert resp.status_code == 302
        assert urlparse(resp.headers["Location"]).path == "/mod/redeem"

    def test_expired_access(self):
        self.giveTeamAdminAccess(expiration_days=-1)
        resp = self.web_client.get("/mod")

        assert resp.status_code == 302
        assert urlparse(resp.headers["Location"]).path == "/mod/redeem"

    def test_nothing_to_review(self):
        self.giveTeamAdminAccess()
        resp = self.web_client.get("/mod")

        assert resp.status_code == 200

    def test_manage_media_expired_auth(self):
        access_key = self.giveTeamAdminAccess()

        team_reference = Media.create_reference("team", "frc1124")
        suggestion_id = self.createSocialMediaSuggestion()
        suggestion = Suggestion.get_by_id(suggestion_id)
        media = MediaCreator.create_media_model(suggestion, team_reference)
        media_key = media.put()
        assert team_reference in media.references

        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()

        resp = self.web_client.post(
            "/mod",
            data={
                "team_number": 1124,
                "action": "remove_media_reference",
                "media_key_name": media_key.id(),
            },
        )

        assert resp.status_code == 403

    def test_remove_social_media_reference(self):
        self.giveTeamAdminAccess()

        team_reference = Media.create_reference("team", "frc1124")
        suggestion_id = self.createSocialMediaSuggestion()
        suggestion = Suggestion.get_by_id(suggestion_id)
        media = MediaCreator.create_media_model(suggestion, team_reference)
        media_key = media.put()
        assert team_reference in media.references

        resp = self.web_client.post(
            "/mod",
            data={
                "team_number": 1124,
                "action": "remove_media_reference",
                "media_key_name": media_key.id(),
            },
        )

        assert resp.status_code == 302

        media = media_key.get()
        assert team_reference not in media.references

    def test_remove_media_reference(self):
        self.giveTeamAdminAccess()

        team_reference = Media.create_reference("team", "frc1124")
        suggestion_id = self.createMediaSuggestion()
        suggestion = Suggestion.get_by_id(suggestion_id)
        media = MediaCreator.create_media_model(suggestion, team_reference)
        media_key = media.put()
        assert team_reference in media.references

        resp = self.web_client.post(
            "/mod",
            data={
                "team_number": 1124,
                "action": "remove_media_reference",
                "media_key_name": media_key.id(),
            },
        )

        assert resp.status_code == 302

        media = media_key.get()
        assert team_reference not in media.references

    def test_make_media_preferred(self):
        self.giveTeamAdminAccess()

        team_reference = Media.create_reference("team", "frc1124")
        suggestion_id = self.createMediaSuggestion()
        suggestion = Suggestion.get_by_id(suggestion_id)
        media = MediaCreator.create_media_model(suggestion, team_reference)
        media_key = media.put()
        assert team_reference in media.references

        resp = self.web_client.post(
            "/mod",
            data={
                "team_number": 1124,
                "action": "add_media_preferred",
                "media_key_name": media_key.id(),
            },
        )

        assert resp.status_code == 302

        media = media_key.get()
        assert team_reference in media.references
        assert team_reference in media.preferred_references

    def test_remove_media_preferred(self):
        self.giveTeamAdminAccess()

        team_reference = Media.create_reference("team", "frc1124")
        suggestion_id = self.createMediaSuggestion()
        suggestion = Suggestion.get_by_id(suggestion_id)
        media = MediaCreator.create_media_model(suggestion, team_reference)
        media.preferred_references.append(team_reference)
        media_id = media.put()
        self.assertTrue(ndb.Key(Team, "frc1124") in media.references)

        self.web_client.post(
            "/mod",
            data={
                "team_number": 1124,
                "action": "remove_media_preferred",
                "media_key_name": media_id.id(),
            },
        )

        media = media_id.get()
        self.assertTrue(team_reference in media.references)
        self.assertFalse(team_reference in media.preferred_references)

    def test_set_robot_name(self):
        self.giveTeamAdminAccess()

        # There is no Robot models that exists yet for this team
        response = self.web_client.post(
            "/mod",
            data={
                "team_number": 1124,
                "action": "set_team_info",
                "robot_name": "Test Robot Name",
            },
        )

        self.assertEqual(response.status_code, 302)
        robot = Robot.get_by_id(Robot.render_key_name("frc1124", self.now.year))
        self.assertIsNotNone(robot)
        self.assertEqual(robot.robot_name, "Test Robot Name")

    def test_update_robot_name(self):
        self.giveTeamAdminAccess()

        Robot(
            id=Robot.render_key_name(self.team.key_name, self.now.year),
            team=self.team.key,
            year=self.now.year,
            robot_name="First Robot Name",
        ).put()

        response = self.web_client.post(
            "/mod",
            data={
                "team_number": 1124,
                "action": "set_team_info",
                "robot_name": "Second Robot Name",
            },
        )

        self.assertEqual(response.status_code, 302)
        robot = Robot.get_by_id(Robot.render_key_name("frc1124", self.now.year))
        self.assertIsNotNone(robot)
        self.assertEqual(robot.robot_name, "Second Robot Name")

    def test_delete_robot_name(self):
        self.giveTeamAdminAccess()

        Robot(
            id=Robot.render_key_name(self.team.key_name, self.now.year),
            team=self.team.key,
            year=self.now.year,
            robot_name="First Robot Name",
        ).put()

        response = self.web_client.post(
            "/mod",
            data={
                "team_number": 1124,
                "action": "set_team_info",
                "robot_name": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        robot = Robot.get_by_id(Robot.render_key_name("frc1124", self.now.year))
        self.assertIsNone(robot)

    def test_accept_team_media_expired_auth(self):
        access_key = self.giveTeamAdminAccess()

        suggestion_id = self.createMediaSuggestion()
        response = self.web_client.get("/mod")
        self.assertEqual(response.status_code, 200)

        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()

        response = self.web_client.post(
            "/mod/review",
            data={
                "accept_reject-{}".format(suggestion_id): "accept::{}".format(
                    suggestion_id
                )
            },
        )
        self.assertEqual(response.status_code, 403)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_PENDING)

    def test_reject_team_media_expired_auth(self):
        access_key = self.giveTeamAdminAccess()

        suggestion_id = self.createMediaSuggestion()
        response = self.web_client.get("/mod")
        self.assertEqual(response.status_code, 200)

        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()

        response = self.web_client.post(
            "/mod/review",
            data={
                "accept_reject-{}".format(suggestion_id): "reject::{}".format(
                    suggestion_id
                )
            },
        )
        self.assertEqual(response.status_code, 403)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_PENDING)

    def test_accept_team_media(self):
        self.giveTeamAdminAccess()

        suggestion_id = self.createMediaSuggestion()

        response = self.web_client.post(
            "/mod/review",
            data={
                "accept_reject-{}".format(suggestion_id): "accept::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 302)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_ACCEPTED)

        medias = Media.query().fetch()
        self.assertEqual(len(medias), 1)
        media = medias[0]
        self.assertIsNotNone(media)
        self.assertEqual(media.foreign_key, "foobar")
        self.assertEqual(media.media_type_enum, MediaType.IMGUR)
        self.assertTrue(ndb.Key(Team, "frc1124") in media.references)

    def test_accept_team_media_as_preferred(self):
        self.giveTeamAdminAccess()

        suggestion_id = self.createMediaSuggestion()
        response = self.web_client.post(
            "/mod/review",
            data={
                "accept_reject-{}".format(suggestion_id): "accept::{}".format(
                    suggestion_id
                ),
                "preferred_keys[]": "preferred::{}".format(suggestion_id),
            },
        )
        self.assertEqual(response.status_code, 302)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_ACCEPTED)

        medias = Media.query().fetch()
        self.assertEqual(len(medias), 1)
        media = medias[0]
        self.assertIsNotNone(media)
        self.assertEqual(media.foreign_key, "foobar")
        self.assertEqual(media.media_type_enum, MediaType.IMGUR)
        self.assertTrue(ndb.Key(Team, "frc1124") in media.preferred_references)

    def test_reject_team_media(self):
        self.giveTeamAdminAccess()

        suggestion_id = self.createMediaSuggestion()
        response = self.web_client.post(
            "/mod/review",
            data={
                "accept_reject-{}".format(suggestion_id): "reject::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 302)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_REJECTED)

        medias = Media.query().fetch()
        self.assertEqual(len(medias), 0)

    def test_accept_social_media_expired_auth(self):
        access_key = self.giveTeamAdminAccess()

        suggestion_id = self.createSocialMediaSuggestion()
        response = self.web_client.get("/mod")
        self.assertEqual(response.status_code, 200)

        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()

        response = self.web_client.post(
            "/mod/review",
            data={
                "accept_reject-{}".format(suggestion_id): "accept::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 403)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_PENDING)

    def test_reject_social_media_expired_auth(self):
        access_key = self.giveTeamAdminAccess()

        suggestion_id = self.createSocialMediaSuggestion()
        response = self.web_client.get("/mod")
        self.assertEqual(response.status_code, 200)

        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()

        response = self.web_client.post(
            "/mod/review",
            data={
                "accept_reject-{}".format(suggestion_id): "reject::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 403)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_PENDING)

    def test_accept_social_media(self):
        self.giveTeamAdminAccess()

        suggestion_id = self.createSocialMediaSuggestion()
        response = self.web_client.post(
            "/mod/review",
            data={
                "accept_reject-{}".format(suggestion_id): "accept::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 302)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_ACCEPTED)

        medias = Media.query().fetch()
        self.assertEqual(len(medias), 1)
        media = medias[0]
        self.assertIsNotNone(media)
        self.assertEqual(media.foreign_key, "frc1124")
        self.assertEqual(media.media_type_enum, MediaType.TWITTER_PROFILE)
        self.assertTrue(ndb.Key(Team, "frc1124") in media.references)

    def test_reject_social_media(self):
        self.giveTeamAdminAccess()

        suggestion_id = self.createSocialMediaSuggestion()
        response = self.web_client.post(
            "/mod/review",
            data={
                "accept_reject-{}".format(suggestion_id): "reject::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 302)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_REJECTED)

        medias = Media.query().fetch()
        self.assertEqual(len(medias), 0)

    def test_accept_robot_design_expired_auth(self):
        access_key = self.giveTeamAdminAccess()

        suggestion_id = self.createDesignSuggestion()
        response = self.web_client.get("/mod")
        self.assertEqual(response.status_code, 200)

        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()

        response = self.web_client.post(
            "/mod/review",
            data={
                "accept_reject-{}".format(suggestion_id): "accept::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 403)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_PENDING)

    def test_reject_robot_design_expired_auth(self):
        access_key = self.giveTeamAdminAccess()

        suggestion_id = self.createDesignSuggestion()
        response = self.web_client.get("/mod")
        self.assertEqual(response.status_code, 200)

        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()

        response = self.web_client.post(
            "/mod/review",
            data={
                "accept_reject-{}".format(suggestion_id): "accept::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 403)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_PENDING)

    def test_accept_robot_design(self):
        self.giveTeamAdminAccess()

        suggestion_id = self.createDesignSuggestion()
        response = self.web_client.post(
            "/mod/review",
            data={
                "accept_reject-{}".format(suggestion_id): "accept::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 302)

        # Make sure the Media object gets created
        media = Media.query().fetch()[0]
        self.assertIsNotNone(media)
        self.assertEqual(media.media_type_enum, MediaType.GRABCAD)
        self.assertEqual(media.year, 2016)
        self.assertListEqual(media.references, [self.team.key])

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_ACCEPTED)

    def test_reject_robot_design(self):
        self.giveTeamAdminAccess()

        suggestion_id = self.createDesignSuggestion()
        response = self.web_client.post(
            "/mod/review",
            data={
                "accept_reject-{}".format(suggestion_id): "reject::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 302)

        # Make sure the Media object doesn't get created
        medias = Media.query().fetch(keys_only=True)
        self.assertEqual(len(medias), 0)

        # Make sure we mark the Suggestion as REVIEWED
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_REJECTED)

    def test_review_redirects_to_mod_dashboard(self):
        self.giveTeamAdminAccess()
        suggestion_id = self.createMediaSuggestion()

        response = self.web_client.post(
            "/mod/review",
            data={f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.headers["Location"]).path, "/mod")

    def test_review_ignores_return_url(self):
        # The retired review controllers redirected to a caller-supplied
        # return_url (an open redirect); the new route always goes home
        self.giveTeamAdminAccess()
        suggestion_id = self.createMediaSuggestion()

        response = self.web_client.post(
            "/mod/review",
            data={
                f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}",
                "return_url": "https://evil.example.com/",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.headers["Location"]).path, "/mod")
        self.assertNotIn("evil.example.com", response.headers["Location"])

    def test_review_other_team_forbidden(self):
        self.giveTeamAdminAccess()  # frc1124
        Team(id="frc254", team_number=254).put()
        status = SuggestionCreator.createTeamMediaSuggestion(
            self.account.account_key,
            "http://imgur.com/other",
            "frc254",
            str(self.now.year),
        ).get_result()
        self.assertEqual(status[0], "success")
        suggestion_id = Suggestion.query().fetch(keys_only=True)[0].id()

        response = self.web_client.post(
            "/mod/review",
            data={f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}"},
        )

        self.assertEqual(response.status_code, 403)
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_PENDING)
        self.assertEqual(len(Media.query().fetch()), 0)

    def test_review_batch_with_one_forbidden_applies_nothing(self):
        self.giveTeamAdminAccess()  # frc1124
        own_id = self.createMediaSuggestion()
        Team(id="frc254", team_number=254).put()
        status = SuggestionCreator.createTeamMediaSuggestion(
            self.account.account_key,
            "http://imgur.com/other",
            "frc254",
            str(self.now.year),
        ).get_result()
        self.assertEqual(status[0], "success")
        other_id = [
            k.id() for k in Suggestion.query().fetch(keys_only=True) if k.id() != own_id
        ][0]

        response = self.web_client.post(
            "/mod/review",
            data={
                f"accept_reject-{own_id}": f"accept::{own_id}",
                f"accept_reject-{other_id}": f"reject::{other_id}",
            },
        )

        self.assertEqual(response.status_code, 403)
        for suggestion_id in (own_id, other_id):
            suggestion = Suggestion.get_by_id(suggestion_id)
            self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_PENDING)
        self.assertEqual(len(Media.query().fetch()), 0)

    def test_review_unknown_suggestion_is_bad_request(self):
        self.giveTeamAdminAccess()

        response = self.web_client.post(
            "/mod/review",
            data={"accept_reject-nope": "accept::nope"},
        )

        self.assertEqual(response.status_code, 400)

    def test_review_with_no_team_access_and_no_permission_forbidden(self):
        suggestion_id = self.createMediaSuggestion()

        response = self.web_client.post(
            "/mod/review",
            data={f"accept_reject-{suggestion_id}": f"reject::{suggestion_id}"},
        )

        self.assertEqual(response.status_code, 403)
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_PENDING)

    def test_review_with_global_permission_needs_no_team_access(self):
        self.account.permissions = [AccountPermission.REVIEW_MEDIA]
        suggestion_id = self.createMediaSuggestion()

        response = self.web_client.post(
            "/mod/review",
            data={f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}"},
        )

        self.assertEqual(response.status_code, 302)
        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_ACCEPTED)
        self.assertEqual(len(Media.query().fetch()), 1)

    def test_accept_team_media_with_year_override(self):
        self.giveTeamAdminAccess()
        suggestion_id = self.createMediaSuggestion()

        response = self.web_client.post(
            "/mod/review",
            data={
                f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}",
                f"year-{suggestion_id}": "2019",
            },
        )

        self.assertEqual(response.status_code, 302)
        medias = Media.query().fetch()
        self.assertEqual(len(medias), 1)
        self.assertEqual(medias[0].year, 2019)

    def test_accept_team_media_writes_audit_log(self):
        self.giveTeamAdminAccess()
        suggestion_id = self.createMediaSuggestion()

        self.web_client.post(
            "/mod/review",
            data={f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}"},
        )

        entries = AuditLogEntry.query().fetch()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].account, self.account.account_key)
        self.assertEqual(entries[0].endpoint, "team_admin.team_mod_review")
        self.assertEqual(entries[0].target_key, ndb.Key(Team, "frc1124"))

    def test_review_media_permission_forced_team_hides_cad(self):
        # A REVIEW_MEDIA holder using ?team=&year= may act on media but not
        # CAD, so the dashboard must not offer CAD rows that would 403
        self.account.has_permission.return_value = True
        self.account.permissions = [AccountPermission.REVIEW_MEDIA]
        media_id = self.createMediaSuggestion()
        design_id = self.createDesignSuggestion()

        response = self.web_client.get(f"/mod?team=1124&year={self.now.year}")

        self.assertEqual(response.status_code, 200)
        self.assertIn(f"accept::{media_id}".encode(), response.data)
        self.assertNotIn(f"accept::{design_id}".encode(), response.data)
        self.assertNotIn(b"Robot CAD Suggestion", response.data)

    def test_review_unapplied_outcome_is_shown_on_dashboard(self):
        self.giveTeamAdminAccess()
        suggestion_id = self.createMediaSuggestion()
        # Someone else got there first
        suggestion = Suggestion.get_by_id(suggestion_id)
        suggestion.review_state = SuggestionState.REVIEW_REJECTED
        suggestion.put()

        response = self.web_client.post(
            "/mod/review",
            data={f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}"},
        )

        self.assertEqual(response.status_code, 302)
        location = urlparse(response.headers["Location"])
        self.assertEqual(location.path, "/mod")
        self.assertIn("review_error=", location.query)
        self.assertIn("already_reviewed", location.query)

        dashboard = self.web_client.get(response.headers["Location"])
        self.assertIn(b'id="review-error"', dashboard.data)
        self.assertIn(b"already_reviewed", dashboard.data)

    def test_review_malformed_keys_are_bad_requests(self):
        self.giveTeamAdminAccess()

        # Empty, too long in bytes, and too long only once UTF-8 encoded
        for key in ("", "x" * 501, "\U0001f600" * 130):
            response = self.web_client.post(
                "/mod/review", data={"accept_reject-1": f"accept::{key}"}
            )
            self.assertEqual(response.status_code, 400)

    def test_review_audit_log_names_the_suggestion(self):
        self.giveTeamAdminAccess()
        suggestion_id = self.createMediaSuggestion()

        self.web_client.post(
            "/mod/review",
            data={f"accept_reject-{suggestion_id}": f"reject::{suggestion_id}"},
        )

        entries = AuditLogEntry.query().fetch()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].url_args, {"suggestion_key": suggestion_id})
        self.assertEqual(entries[0].target_key, ndb.Key(Team, "frc1124"))

    def test_review_returns_forced_team_viewer_to_their_view(self):
        # A REVIEW_MEDIA holder with no TeamAdminAccess rows arrived via
        # ?team=&year=; a bare /mod would bounce them to /mod/redeem
        self.account.has_permission.return_value = True
        self.account.permissions = [AccountPermission.REVIEW_MEDIA]
        suggestion_id = self.createMediaSuggestion()

        page = self.web_client.get(f"/mod?team=1124&year={self.now.year}")
        self.assertIn(b'name="team" value="1124"', page.data)

        response = self.web_client.post(
            "/mod/review",
            data={
                f"accept_reject-{suggestion_id}": f"accept::{suggestion_id}",
                "team": "1124",
                "year": str(self.now.year),
            },
        )

        self.assertEqual(response.status_code, 302)
        location = urlparse(response.headers["Location"])
        self.assertEqual(location.path, "/mod")
        self.assertIn("team=1124", location.query)
        self.assertIn(f"year={self.now.year}", location.query)
        dashboard = self.web_client.get(response.headers["Location"])
        self.assertEqual(dashboard.status_code, 200)

    def test_review_reports_every_unapplied_outcome(self):
        self.giveTeamAdminAccess()
        first_id = self.createMediaSuggestion()
        Team(id="frc1124", team_number=1124).put()
        status = SuggestionCreator.createTeamMediaSuggestion(
            self.account.account_key,
            "http://imgur.com/second",
            "frc1124",
            str(self.now.year),
        ).get_result()
        self.assertEqual(status[0], "success")
        second_id = [
            k.id()
            for k in Suggestion.query().fetch(keys_only=True)
            if k.id() != first_id
        ][0]
        for suggestion_id in (first_id, second_id):
            suggestion = Suggestion.get_by_id(suggestion_id)
            suggestion.review_state = SuggestionState.REVIEW_REJECTED
            suggestion.put()

        response = self.web_client.post(
            "/mod/review",
            data={
                f"accept_reject-{first_id}": f"accept::{first_id}",
                f"accept_reject-{second_id}": f"reject::{second_id}",
            },
        )

        location = urlparse(response.headers["Location"])
        self.assertIn(first_id, location.query)
        self.assertIn(second_id, location.query)
