from datetime import timedelta

from flask import render_template

from backend.common.decorators import cached_public


@cached_public(ttl=timedelta(weeks=1))
def brand() -> str:
    return render_template("brand.html")
