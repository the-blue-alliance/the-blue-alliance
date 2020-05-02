import pkg_resources
from google.appengine.ext import vendor

path = 'lib'
vendor.add(path)
pkg_resources.working_set.add_entry(path)


# https://stackoverflow.com/a/59334563
import six; reload(six)
