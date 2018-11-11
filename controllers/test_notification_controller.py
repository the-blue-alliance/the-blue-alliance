import logging

from consts.notification_type import NotificationType
from base_controller import LoggedInHandler
from helpers.push_helper import PushHelper
from models.district import District
from models.match import Match
from models.event import Event

from notifications.alliance_selections import AllianceSelectionNotification
from notifications.awards_updated import AwardsUpdatedNotification
from notifications.district_points_updated import DistrictPointsUpdatedNotification
from notifications.level_starting import CompLevelStartingNotification
from notifications.match_score import MatchScoreNotification
from notifications.match_video import MatchVideoNotification, EventMatchVideoNotification
from notifications.schedule_updated import ScheduleUpdatedNotification
from notifications.upcoming_match import UpcomingMatchNotification

"""
Send out a static notification of each type to
all of a user's devices. Used to test parsing
incoming notifications
"""


class TestNotificationController(LoggedInHandler):
    def post(self, type):
        self._require_registration('/account/')
        event_key = self.request.get('event_key')
        match_key = self.request.get('match_key')
        district_key = self.request.get('district_key')
        user_id = self.user_bundle.account.key.id()

        logging.info("Sending for {}".format(type))
        try:
            type = int(type)
        except ValueError:
            # Not passed a valid int, just stop here
            logging.info("Invalid number passed")
            return

        event = None

        if type != NotificationType.DISTRICT_POINTS_UPDATED:
            if event_key == "":
                logging.info("No event key")
                self.response.out.write("No event key specified!")
                return

            event = Event.get_by_id(event_key)

            if event is None:
                logging.info("Invalid event key passed")
                self.response.out.write("Invalid event key!")
                return

        if type == NotificationType.UPCOMING_MATCH:
            if match_key == "":
                logging.info("No match key")
                self.response.out.write("No match key specified!")
                return

            match = Match.get_by_id(match_key)

            if match is None:
                logging.info("Invalid match key passed")
                self.response.out.write("Invalid match key!")
                return

            notification = UpcomingMatchNotification(match, event)
        elif type == NotificationType.MATCH_SCORE:
            if match_key == "":
                logging.info("No match key")
                self.response.out.write("No match key specified!")
                return

            match = Match.get_by_id(match_key)

            if match is None:
                logging.info("Invalid match key passed")
                self.response.out.write("Invalid match key!")
                return

            notification = MatchScoreNotification(match)
        elif type == NotificationType.LEVEL_STARTING:
            if match_key == "":
                logging.info("No match key")
                self.response.out.write("No match key specified!")
                return

            match = Match.get_by_id(match_key)

            if match is None:
                logging.info("Invalid match key passed")
                self.response.out.write("Invalid match key!")
                return

            notification = CompLevelStartingNotification(match, event)
        elif type == NotificationType.ALLIANCE_SELECTION:
            notification = AllianceSelectionNotification(event)
        elif type == NotificationType.AWARDS:
            notification = AwardsUpdatedNotification(event)
        elif type == NotificationType.MEDIA_POSTED:
            # Not implemented yet
            pass
        elif type == NotificationType.DISTRICT_POINTS_UPDATED:
            if district_key == "":
                logging.info("No district key")
                self.response.out.write("No district key specified!")
                return

            district = District.get_by_id(district_key)

            if district is None:
                logging.info("Invalid district key passed")
                self.response.out.write("Invalid district key!")
                return
            notification = DistrictPointsUpdatedNotification(district)
        elif type == NotificationType.SCHEDULE_UPDATED:
            if match_key == "":
                logging.info("No match key")
                self.response.out.write("No match key specified!")
                return

            match = Match.get_by_id(match_key)

            if match is None:
                logging.info("Invalid match key passed")
                self.response.out.write("Invalid match key!")
                return

            notification = ScheduleUpdatedNotification(event, match)
        elif type == NotificationType.FINAL_RESULTS:
            # Not implemented yet
            pass
        elif type == NotificationType.MATCH_VIDEO:
            if match_key == "":
                logging.info("No match key")
                self.response.out.write("No match key specified!")
                return

            match = Match.get_by_id(match_key)

            if match is None:
                logging.info("Invalid match key passed")
                self.response.out.write("Invalid match key!")
                return

            notification = MatchVideoNotification(match)
        elif type == NotificationType.EVENT_MATCH_VIDEO:
            if match_key == "":
                logging.info("No match key")
                self.response.out.write("No match key specified!")
                return

            match = Match.get_by_id(match_key)

            if match is None:
                logging.info("Invalid match key passed")
                self.response.out.write("Invalid match key!")
                return

            notification = EventMatchVideoNotification(match)
        else:
            # Not passed a valid int, return
            return

        keys = PushHelper.get_client_ids_for_users([user_id])
        logging.info("Keys: {}".format(keys))
        if notification:
            # This page should not push notifications to the firebase queue
            # Nor should its notifications be tracked in analytics
            notification.send(keys, push_firebase=False, track_call=False)

        self.response.out.write("ok")