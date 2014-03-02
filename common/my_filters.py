from google.appengine.ext import webapp
import re

# More info on custom Django template filters here:
# https://docs.djangoproject.com/en/dev/howto/custom-template-tags/#registering-custom-filters

register = webapp.template.create_template_register()


@register.filter
def digits(value):
    return re.sub('[^0-9]', '', value)

@register.filter(name='user_gameday_selection')
def user_gameday_selection(current,value):
    if current is value:
        return "selected"
    else:
    		return ""
