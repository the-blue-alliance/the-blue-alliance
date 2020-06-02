from flask import render_template


def gameday() -> str:
    return render_template("gameday2.html", webcasts_json={}, default_chat=None)
