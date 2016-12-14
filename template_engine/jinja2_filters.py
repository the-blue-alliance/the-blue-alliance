from email import utils
import math
import re
import time
import urllib


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


def slugify(value):
    from django.template.defaultfilters import slugify as django_slugify
    return django_slugify(value)
