from google.appengine.ext import webapp
import re

# More info on custom Django template filters here:
# https://docs.djangoproject.com/en/dev/howto/custom-template-tags/#registering-custom-filters

register = webapp.template.create_template_register()

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


@register.filter(name="defense_name")
def defense_name(value):
    if value in defense_render_names_2016:
        return defense_render_names_2016[value]
    return value


@register.filter
def digits(value):
    return re.sub('[^0-9]', '', value)


@register.filter
def mul(value, arg):
    return value * arg
