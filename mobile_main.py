import webapp2

import tba_config

from controllers.mobile_controller import MobileRegistrationController, MobileTestMessageController

app = webapp2.WSGIApplication([
                                webapp2.Route(r'/mobile/register',
                                MobileRegistrationController,
                                methods=['POST']),

                                webapp2.Route(r'/mobile/test_message',
                                MobileTestMessageController,
                                methods=['GET'])

                                ], debug=tba_config.DEBUG)
