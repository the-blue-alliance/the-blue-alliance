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
            extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_'],
            autoescape=True)
    else:
        logging.info("Using jinja2.FileSystemLoader")
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), '../templates_jinja2')),
            extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_'],
            autoescape=True)
    env.filters['ceil'] = jinja2_filters.ceil
    env.filters['defense_name'] = jinja2_filters.defense_name
    env.filters['digits'] = jinja2_filters.digits
    env.filters['floatformat'] = jinja2_filters.floatformat
    env.filters['isoformat'] = jinja2_filters.isoformat
    env.filters['limit_prob'] = jinja2_filters.limit_prob
    env.filters['union'] = jinja2_filters.union
    env.filters['strftime'] = jinja2_filters.strftime
    env.filters['strip_frc'] = jinja2_filters.strip_frc
    env.filters['urlencode'] = jinja2_filters.urlencode
    env.filters['rfc2822'] = jinja2_filters.rfc2822
    env.filters['slugify'] = jinja2_filters.slugify
    env.filters['yt_start'] = jinja2_filters.yt_start
    env.filters['match_short'] = jinja2_filters.match_short
    return env


JINJA_ENV = get_jinja_env()  # Set up instance cache


def render(template, template_values):
    from stackdriver.profiler import TraceContext
    with TraceContext() as root:
        with root.span("jinja2_engine.render({})".format(template)):
            template = JINJA_ENV.get_template(template)
            return template.render(template_values)
