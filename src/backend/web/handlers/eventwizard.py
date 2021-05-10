from flask import render_template

from backend.common.decorators import cached_public


@cached_public(timeout=int(60 * 60))
def eventwizard2() -> str:
    return render_template("react-eventwizard.html")
