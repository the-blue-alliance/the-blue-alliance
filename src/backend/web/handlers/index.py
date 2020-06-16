from flask import render_template

from backend.common.decorators import cached_public


@cached_public
def index() -> str:
    return render_template("base.html")
