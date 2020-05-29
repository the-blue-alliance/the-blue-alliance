from flask import render_template
from common import helpers


def HomeHandler() -> str:
    return render_template("base.html")
