from flask import render_template
from backend.common.profiler import Span


def render(template, **template_values):
    with Span("render_template"):
        render_template(template, template_values)
