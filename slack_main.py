import webapp2

import tba_config

from controllers.slack_controller import ModQueue


app = webapp2.WSGIApplication([('/slack/modqueue', ModQueueHandler),
                               ],
                              debug=tba_config.DEBUG)
