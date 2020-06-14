from flask import render_template as flask_render_template

from backend.common.profiler import Span


def render_template(template, template_values):
    with Span("render_template"):
        return flask_render_template(template, **template_values)
