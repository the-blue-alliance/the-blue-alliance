from google.appengine.ext import webapp
from helpers.youtube_video_helper import YouTubeVideoHelper
import re

# More info on custom Django template filters here:
# https://docs.djangoproject.com/en/dev/howto/custom-template-tags/#registering-custom-filters

register = webapp.template.create_template_register()


@register.filter
def batch(iterable, n):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


@register.filter
def digits(value):
    return re.sub('[^0-9]', '', value)


@register.filter
def mul(value, arg):
    return value * arg


@register.filter
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


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
