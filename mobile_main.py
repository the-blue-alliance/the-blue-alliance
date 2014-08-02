import webapp2

import tba_config

from controllers.mobile_controller import MobileRegistrationController, MobileTestMessageController, \
                                          AddFavoriteController, RemoveFavoriteController, GetFavoritesController, \
                                          MobileTokenUpdateController, MobileTokenDeleteController

app = webapp2.WSGIApplication([
                                webapp2.Route(r'/mobile/register',
                                MobileRegistrationController,
                                methods=['POST']),

                                webapp2.Route(r'/mobile/favorites',
                                GetFavoritesController,
                                methods=['POST']),

                                webapp2.Route(r'/mobile/favorite/add',
                                AddFavoriteController,
                                methods=['POST']),

                                webapp2.Route(r'/mobile/favorite/remove',
                                RemoveFavoriteController,
                                methods=['POST']),

                                # ALL ENDPOINT BELOW THIS LINE ARE TESTS AND SHOULD BE REMOVED (eventually)

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
