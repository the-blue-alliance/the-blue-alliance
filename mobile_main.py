import webapp2

import tba_config

<<<<<<< Updated upstream
from controllers.mobile_controller import MobileRegistrationController, MobileTestMessageController
=======
from controllers.mobile_controller import MobileRegistrationController, MobileTestMessageController, \
                                          AddFavoriteController, MobileTokenUpdateController, MobileTokenDeleteController
>>>>>>> Stashed changes

app = webapp2.WSGIApplication([
                                webapp2.Route(r'/mobile/register',
                                MobileRegistrationController,
                                methods=['POST'], strict_slash=True),

                                webapp2.Route(r'/mobile/test_message',
                                MobileTestMessageController,
                                methods=['GET']),

                                webapp2.Route(r'/mobile/update_token',
                                MobileTokenUpdateController,
                                methods=['GET']),

                                webapp2.Route(r'/mobile/delete_token',
                                MobileTokenDeleteController,
                                methods=['GET'])

                                ], debug=tba_config.DEBUG)
