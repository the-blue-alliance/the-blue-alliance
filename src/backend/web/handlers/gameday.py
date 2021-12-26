from datetime import timedelta

from flask import render_template

from backend.common.decorators import cached_public


@cached_public(ttl=timedelta(seconds=61))
def gameday() -> str:
    return render_template("gameday2.html", webcasts_json={}, default_chat=None)
