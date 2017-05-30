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
    def get(self, type):
        self._require_registration('/account/')
        user_id = self.user_bundle.account.key.id()

        logging.info("Sending for {}".format(type))
        try:
            type = int(type)
        except ValueError:
            # Not passed a valid int, just stop here
            logging.info("Invalid number passed")
            self.redirect('/apidocs/webhooks')
            return

        event = Event.get_by_id('2014necmp')
        match = Match.get_by_id('2014necmp_f1m1')
        district = District.get_by_id('2014ne')

        if type == NotificationType.UPCOMING_MATCH:
            notification = UpcomingMatchNotification(match, event)
        elif type == NotificationType.MATCH_SCORE:
            notification = MatchScoreNotification(match)
        elif type == NotificationType.LEVEL_STARTING:
            notification = CompLevelStartingNotification(match, event)
        elif type == NotificationType.ALLIANCE_SELECTION:
            notification = AllianceSelectionNotification(event)
        elif type == NotificationType.AWARDS:
            notification = AwardsUpdatedNotification(event)
        elif type == NotificationType.MEDIA_POSTED:
            # Not implemented yet
            pass
        elif type == NotificationType.DISTRICT_POINTS_UPDATED:
            notification = DistrictPointsUpdatedNotification(district)
        elif type == NotificationType.SCHEDULE_UPDATED:
            notification = ScheduleUpdatedNotification(event, match)
        elif type == NotificationType.FINAL_RESULTS:
            # Not implemented yet
            pass
        elif type == NotificationType.MATCH_VIDEO:
            notification = MatchVideoNotification(match)
        elif type == NotificationType.EVENT_MATCH_VIDEO:
            notification = EventMatchVideoNotification(match)
        else:
            # Not passed a valid int, return
            self.redirect('/apidocs/webhooks')
            return

        keys = PushHelper.get_client_ids_for_users([user_id])
        logging.info("Keys: {}".format(keys))
        if notification:
            # This page should not push notifications to the firebase queue
            # Nor should its notifications be tracked in analytics
            notification.send(keys, push_firebase=False, track_call=False)

        self.redirect('/apidocs/webhooks')
