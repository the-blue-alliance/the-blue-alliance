from email import utils
import re
import time
import urllib


def digits(s):
    if not s:
        return ''
    if type(s) is int:
        return s
    return re.sub('[^0-9]', '', s)


def floatformat(num, num_decimals):
    return "%.{}f".format(num_decimals) % num


def strftime(datetime, formatstr):
    """
    Uses Python's strftime with some tweaks
    """
    return datetime.strftime(formatstr).lstrip("0").replace(" 0", " ")


def strip_frc(s):
    if not s:
        return ''
    return s[3:]


def urlencode(s):
    return urllib.quote(s.encode('utf8'))


def rfc2822(datetime):
    tt = datetime.timetuple()
    timestamp = time.mktime(tt)
    return utils.formatdate(timestamp)
