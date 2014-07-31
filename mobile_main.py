import webapp2

import tba_config

from controllers.mobile_controller import MobileRegistrationController

app = webapp2.WSGIApplication([
                                webapp2.Route(r'/mobile/register',
                                MobileRegistrationController,
                                methods=['POST'])

                                ], debug=tba_config.DEBUG)
