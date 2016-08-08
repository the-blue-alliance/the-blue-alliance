import jinja2
import logging
import os
import tba_config

from template_engine import jinja2_filters


def get_jinja_env(force_filesystemloader=False):
    if tba_config.CONFIG['use-compiled-templates'] and not force_filesystemloader:
        logging.info("Using jinja2.ModuleLoader")
        env = jinja2.Environment(
            auto_reload=False,
            loader=jinja2.ModuleLoader(os.path.join(os.path.dirname(__file__), '../templates_jinja2_compiled.zip')),
            extensions=['jinja2.ext.autoescape'],
            autoescape=True)
    else:
        logging.info("Using jinja2.FileSystemLoader")
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '../templates_jinja2')),
            extensions=['jinja2.ext.autoescape'],
            autoescape=True)
    env.filters['defense_name'] = jinja2_filters.defense_name
    env.filters['digits'] = jinja2_filters.digits
    env.filters['floatformat'] = jinja2_filters.floatformat
    env.filters['strftime'] = jinja2_filters.strftime
    env.filters['strip_frc'] = jinja2_filters.strip_frc
    env.filters['urlencode'] = jinja2_filters.urlencode
    env.filters['rfc2822'] = jinja2_filters.rfc2822
    env.filters['slugify'] = jinja2_filters.slugify
    return env


JINJA_ENV = get_jinja_env()  # Set up instance cache


def render(template, template_values):
    template = JINJA_ENV.get_template(template)
    return template.render(template_values)
