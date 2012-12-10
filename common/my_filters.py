from google.appengine.ext import webapp
import re

register = webapp.template.create_template_register()

@register.filter
def digits(value):
    return re.sub('[^0-9]', '', value)