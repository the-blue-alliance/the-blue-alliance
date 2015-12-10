import re
import time
import urllib

from django.template import defaultfilters
from email import utils


def digits(s):
    return re.sub('[^0-9]', '', s)


def floatformat(num, num_decimals):
    return "%.{}f".format(num_decimals) % num


def strftime(datetime, formatstr):
    """
    Uses Python's strftime with some tweaks
    """
    return datetime.strftime(formatstr).lstrip("0").replace(" 0", " ")


def strip_frc(s):
    return s[3:]


def urlencode(s):
    return urllib.quote(s.encode('utf8'))


# def rfc2822(datetime):
#     tt = datetime.timetuple()
#     timestamp = time.mktime(tt)
#     return utils.formatdate(timestamp)


# def slugify(s):
#     """
#     Use Django's slugify method
#     """
#     return defaultfilters.slugify(s)

