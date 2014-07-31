mport webapp2

import tba_config

from controllers.notification_controller import NotificationRegistrationController

app = webapp2.WSGIApplication([
                                webapp2.Route(r'/notifications/register',
                                NotificationRegistrationController,
                                methods=['POST'])

                                ], debug=tba_config.DEBUG)
