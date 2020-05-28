from email import utils
import math
import re
import time
import urllib

from helpers.youtube_video_helper import YouTubeVideoHelper
from models.match import Match

defense_render_names_2016 = {
    'A_ChevalDeFrise': 'Cheval De Frise',
    'A_Portcullis': 'Portcullis',
    'B_Ramparts': 'Ramparts',
    'B_Moat': 'Moat',
    'C_SallyPort': 'Sally Port',
    'C_Drawbridge': 'Drawbridge',
    'D_RoughTerrain': 'Rough Terrain',
    'D_RockWall': 'Rock Wall'
}


def ceil(value):
    return int(math.ceil(value))


def defense_name(value):
    if value in defense_render_names_2016:
        return defense_render_names_2016[value]
    return value


def digits(s):
    if not s:
        return ''
    if type(s) is int:
        return s
    return re.sub('[^0-9]', '', s)


def floatformat(num, num_decimals):
    return "%.{}f".format(num_decimals) % num


def isoformat(datetime):
    return datetime.isoformat()


def union(one, two):
    return set(one) | set(two)


def limit_prob(prob):
    prob *= 100
    prob = min(95, max(prob, 5))
    return int(round(prob))


def strftime(datetime, formatstr):
    """
    Uses Python's strftime with some tweaks
    """

    # https://github.com/django/django/blob/54ea290e5bbd19d87bd8dba807738eeeaf01a362/django/utils/dateformat.py#L289
    def t(day):
        "English ordinal suffix for the day of the month, 2 characters; i.e. 'st', 'nd', 'rd' or 'th'"
        if day in (11, 12, 13):  # Special case
            return 'th'
        last = day % 10
        if last == 1:
            return 'st'
        if last == 2:
            return 'nd'
        if last == 3:
            return 'rd'
        return 'th'

    formatstr = formatstr.replace('%t', t(datetime.day))
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


def slugify(value):
    from django.template.defaultfilters import slugify as django_slugify
    return django_slugify(value)


def yt_start(value):
    if '?t=' in value:  # Treat ?t= the same as #t=
        value = value.replace('?t=', '#t=')
    if '#t=' in value:
        sp = value.split('#t=')
        video_id = sp[0]
        old_ts = sp[1]
        total_seconds = YouTubeVideoHelper.time_to_seconds(old_ts)
        value = '%s?start=%i' % (video_id, total_seconds)

    return value


def match_short(match_key):
    if not Match.validate_key_name(match_key):
        return ''
    match_id = match_key.split('_')[1]
    if match_id.startswith('qm'):
        return 'Q{}'.format(match_id[2:])
    return match_id.replace('m', '-').upper()
