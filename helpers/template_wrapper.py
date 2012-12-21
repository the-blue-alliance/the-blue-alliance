from google.appengine.ext.webapp import template
import tba_config


class TemplateWrapper(object):
    """
    Renders the template at the given path with the given dict of values
    in addition to any global variables.
    """
    @classmethod
    def renderBasePage(self, template_path, template_vars={}):
        template_vars['BASE_CSS'] = tba_config.CONFIG['MAIN_CSS']
        template_vars['BASE_JS'] = tba_config.CONFIG['MAIN_JS']
        return template.render(template_path, template_vars)

    @classmethod
    def renderGamedayPage(self, template_path, template_vars={}):
        template_vars['GAMEDAY_CSS'] = tba_config.CONFIG['GAMEDAY_CSS']
        template_vars['GAMEDAY_JS'] = tba_config.CONFIG['GAMEDAY_JS']
        return template.render(template_path, template_vars)
