import datetime
import logging
import tba_config
from collections import defaultdict

from base_controller import CacheableHandler, LoggedInHandler
from database import media_query
from google.appengine.ext import ndb
from helpers.media_manipulator import MediaManipulator
from helpers.robot_manipulator import RobotManipulator
from helpers.media_helper import MediaHelper
from models.media import Media
from models.robot import Robot
from models.suggestion import Suggestion
from models.team import Team
from models.team_admin_access import TeamAdminAccess
from template_engine import jinja2_engine


class TeamAdminDashboard(LoggedInHandler):
    ALLOWED_SUGGESTION_TYPES = ["media", "social-media", "robot"]
    SUGGESTION_NAMES = {
        "media": "Media",
        "social-media": "Social Media",
        "robot": "Robot CAD",
    }
    SUGGESTION_REVIEW_URL = {
        "media": "/suggest/team/media/review",
        "social-media": "/suggest/team/social/review",
        "robot": "/suggest/cad/review",
    }

    def get(self):
        self._require_registration()
        user = self.user_bundle.account.key

        now = datetime.datetime.now()
        existing_access = TeamAdminAccess.query(
            TeamAdminAccess.account == user,
            TeamAdminAccess.expiration > now).fetch()

        # If the current user is an admin, allow them to view this page for any
        # team/year combination
        forced_team = self.request.get("team")
        forced_year = self.request.get("year")
        if self.user_bundle.is_current_user_admin and forced_team and forced_year:
            existing_access.append(
                TeamAdminAccess(
                    team_number=int(forced_team),
                    year=int(forced_year),
                )
            )

        team_keys = [
            ndb.Key(Team, "frc{}".format(access.team_number))
            for access in existing_access
        ]
        if not team_keys:
            self.redirect('/mod/redeem')
            return
        years = set([access.year for access in existing_access])
        teams_future = ndb.get_multi_async(team_keys)
        robot_keys = [
            ndb.Key(Robot, Robot.renderKeyName(team.id(), now.year)) for team in team_keys
        ]
        robots_future = ndb.get_multi_async(robot_keys)
        social_media_futures = [
            media_query.TeamSocialMediaQuery(team_key.id()).fetch_async()
            for team_key in team_keys
        ]
        team_medias_future = Media.query(
            Media.references.IN(team_keys),
            Media.year.IN(years)).fetch_async(50)
        suggestions_future = Suggestion.query(
            Suggestion.review_state == Suggestion.REVIEW_PENDING).filter(
                Suggestion.target_model.IN(
                    self.ALLOWED_SUGGESTION_TYPES)).filter(
                        Suggestion.target_key.IN([k.id() for k in team_keys
                                                  ])).fetch_async(limit=50)

        team_num_to_team = {
            team.get_result().team_number: team.get_result()
            for team in teams_future
        }
        team_num_to_robot_name = {
            int(robot.get_result().team.id()[3:]): robot.get_result().robot_name
            for robot in robots_future if robot.get_result() is not None
        }
        team_medias = defaultdict(lambda: defaultdict(list))
        for media in team_medias_future.get_result():
            for reference in media.references:
                if reference in team_keys:
                    team_num = reference.id()[3:]
                    team_medias[int(team_num)][media.year].append(media)

        team_social_medias = defaultdict(list)
        for team_social_media_future in social_media_futures:
            social_medias = team_social_media_future.get_result()
            for media in social_medias:
                for reference in media.references:
                    if reference in team_keys:
                        team_num = reference.id()[3:]
                        team_social_medias[int(team_num)].append(media)

        suggestions_by_team = defaultdict(lambda: defaultdict(list))
        for suggestion in suggestions_future.get_result():
            if not suggestion.target_key:
                continue
            # Assume all the keys are team keys
            team_num = suggestion.target_key[3:]
            suggestions_by_team[int(team_num)][suggestion.target_model].append(
                suggestion)

        self.template_values.update({
            "existing_access": existing_access,
            "teams": team_num_to_team,
            "robot_names_by_team": team_num_to_robot_name,
            "team_medias": team_medias,
            "team_social_medias": team_social_medias,
            "suggestions_by_team": suggestions_by_team,
            "suggestion_names": self.SUGGESTION_NAMES,
            "suggestion_review_urls": self.SUGGESTION_REVIEW_URL,
        })

        self.response.out.write(
            jinja2_engine.render('team_admin_dashboard.html',
                                 self.template_values))

    def post(self):
        team_number = self.request.get("team_number")
        if not team_number:
            self.abort(400)
        team_number = int(team_number)
        team = Team.get_by_id("frc{}".format(team_number))
        if not team:
            self.abort(400)
        self._require_team_admin_access(team_number)

        action = self.request.get('action')
        if action == "remove_media_reference":
            media, team_ref = self.get_media_and_team_ref(team_number)
            if team_ref in media.references:
                media.references.remove(team_ref)
            if team_ref in media.preferred_references:
                media.preferred_references.remove(team_ref)
            MediaManipulator.createOrUpdate(media, auto_union=False)
        elif action == "remove_media_preferred":
            media, team_ref = self.get_media_and_team_ref(team_number)
            if team_ref in media.preferred_references:
                media.preferred_references.remove(team_ref)
            MediaManipulator.createOrUpdate(media, auto_union=False)
        elif action == "add_media_preferred":
            media, team_ref = self.get_media_and_team_ref(team_number)
            if team_ref not in media.preferred_references:
                media.preferred_references.append(team_ref)
            MediaManipulator.createOrUpdate(media, auto_union=False)
        elif action == "set_team_info":
            robot_name = self.request.get("robot_name").strip()
            current_year = datetime.datetime.now().year
            robot_key = Robot.renderKeyName(team.key_name, current_year)
            if robot_name:
                robot = Robot(
                    id=robot_key,
                    team=team.key,
                    year=current_year,
                    robot_name=robot_name,
                )
                RobotManipulator.createOrUpdate(robot)
            else:
                RobotManipulator.delete_keys([ndb.Key(Robot, robot_key)])
        else:
            self.abort(400)

        self.redirect('/mod/')

    def get_media_and_team_ref(self, team_number):
        media_key_name = self.request.get("media_key_name")
        media = Media.get_by_id(media_key_name)
        if not media:
            self.abort(400)
        team_ref = Media.create_reference('team', 'frc{}'.format(team_number))
        return media, team_ref


class TeamAdminRedeem(LoggedInHandler):
    def get(self):
        self._require_registration()
        user = self.user_bundle.account.key

        existing_access = TeamAdminAccess.query(
            TeamAdminAccess.account == user).fetch()

        team_keys = [
            ndb.Key(Team, "frc{}".format(access.team_number))
            for access in existing_access
        ]
        teams = ndb.get_multi(team_keys)
        team_num_to_team = {team.team_number: team for team in teams}

        self.template_values.update({
            "existing_access": existing_access,
            "status": self.request.get("status"),
            "team": self.request.get("team"),
            "teams": team_num_to_team,
        })

        self.response.out.write(
            jinja2_engine.render('team_admin_redeem.html',
                                 self.template_values))

    def post(self):
        self._require_registration()
        user = self.user_bundle.account.key

        team_number = self.request.get("team_number")
        if not team_number or not team_number.isdigit():
            self.redirect('/mod/redeem?status=invalid_code')
            return
        team_number = int(team_number)
        auth_code = self.request.get("auth_code").strip()
        access = TeamAdminAccess.query(
            TeamAdminAccess.team_number == team_number,
            TeamAdminAccess.access_code == auth_code).fetch(1)
        if not access:
            self.redirect('/mod/redeem?status=invalid_code')
            return

        access = access[0]
        if access.account:
            self.redirect('/mod/redeem?status=code_used')
            return
        access.account = user
        access.put()

        self.redirect('/mod/redeem?status=success&team={}'.format(
            access.team_number))
