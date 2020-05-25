from google.appengine.ext import vendor

import six
# https://github.com/googleapis/python-ndb/issues/249#issuecomment-560957294
six.moves.reload_module(six)

vendor.add('lib')
