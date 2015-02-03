from consts.notification_type import NotificationType
from base_controller import LoggedInHandler


'''
Send out a static notification of each type to
all of a user's devices. Used to test parsing
incoming notifications
'''
class TestNotificationController(LoggedInHandler):
    def get(self):
        self._require_login('/account/')

        try:
            type = int(self.request.get('type'))
        except ValueError:
            # Not passed a valid int, just stop here
            self.redirect('/apidocs/webhooks')
            return

        if type == NotificationType.UPCOMING_MATCH:
            
        elif type == NotificationType.MATCH_SCORE:

        elif type == NotificationType.LEVEL_STARTING:

        elif type == NotificationType.ALLIANCE_SELECTION:

        elif type == NotificationType.AWARDS:

        elif type == NotificationType.MEDIA_POSTED:

        elif type == NotificationType.DISTRICT_POINTS_UPDATED:

        elif type == NotificationType.SCHEDULE_POSTED:

        elif type == NotificationType.FINAL_RESULTS:

        else:
            # Not passed a valid int, return
            self.redirect('/apidocs/webhooks')
            return
