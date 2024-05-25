import datetime
import json
import unittest
from typing import Optional
from urllib.parse import urlparse

import pytest
from flask.testing import FlaskClient
from google.appengine.ext import ndb

from backend.common.consts.media_type import MediaType
from backend.common.consts.suggestion_state import SuggestionState
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


@pytest.fixture()
def mock_grabcad_api(monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_grabcad_dict(url: str) -> SuggestionDict:
        return SuggestionDict(
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
        )
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
        )
        self.assertEqual(status[0], "success")
        return Suggestion.query().fetch(keys_only=True)[0].id()

    def createDesignSuggestion(self):
        status = SuggestionCreator.createTeamMediaSuggestion(
            self.account.account_key,
            "https://grabcad.com/library/2016-148-robowranglers-1",
            "frc1124",
            "2016",
        )
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
            "/suggest/team/media/review",
            data={
                "accept_reject-{}".format(suggestion_id): "accept::{}".format(
                    suggestion_id
                )
            },
        )

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
            "/suggest/team/media/review",
            data={
                "accept_reject-{}".format(suggestion_id): "reject::{}".format(
                    suggestion_id
                )
            },
        )

        access = access_key.get()
        access.expiration += datetime.timedelta(days=-7)
        access.put()

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_PENDING)

    def test_accept_team_media(self):
        self.giveTeamAdminAccess()

        suggestion_id = self.createMediaSuggestion()

        response = self.web_client.post(
            "/suggest/team/media/review",
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
            "/suggest/team/media/review",
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
            "/suggest/team/media/review",
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
            "/suggest/team/social/review",
            data={
                "accept_reject-{}".format(suggestion_id): "accept::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 401)

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
            "/suggest/team/social/review",
            data={
                "accept_reject-{}".format(suggestion_id): "reject::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 401)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_PENDING)

    def test_accept_social_media(self):
        self.giveTeamAdminAccess()

        suggestion_id = self.createSocialMediaSuggestion()
        response = self.web_client.post(
            "/suggest/team/social/review",
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
            "/suggest/team/social/review",
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
            "/suggest/cad/review",
            data={
                "accept_reject-{}".format(suggestion_id): "accept::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 401)

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
            "/suggest/cad/review",
            data={
                "accept_reject-{}".format(suggestion_id): "accept::{}".format(
                    suggestion_id
                ),
            },
        )
        self.assertEqual(response.status_code, 401)

        suggestion = Suggestion.get_by_id(suggestion_id)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.review_state, SuggestionState.REVIEW_PENDING)

    def test_accept_robot_design(self):
        self.giveTeamAdminAccess()

        suggestion_id = self.createDesignSuggestion()
        response = self.web_client.post(
            "/suggest/cad/review",
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
            "/suggest/cad/review",
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
