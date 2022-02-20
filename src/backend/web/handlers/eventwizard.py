from datetime import datetime, timedelta

from flask import render_template

from backend.common.decorators import cached_public

@cached_public(ttl=timedelta(seconds=61))
def eventwizard() -> str:
    return render_template("eventwizard.html")
