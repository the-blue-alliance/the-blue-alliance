import json
from datetime import timedelta

from flask import render_template

from backend.common.decorators import cached_public
from backend.common.sitevars.gameday_special_webcasts import GamedaySpecialWebcasts


@cached_public(ttl=timedelta(seconds=61))
def gameday() -> str:
    webcasts_json = json.dumps(
        {
            "special_webcasts": GamedaySpecialWebcasts.webcasts(),
        }
    )
    default_chat = GamedaySpecialWebcasts.default_chat()
    return render_template(
        "gameday2.html", webcasts_json=webcasts_json, default_chat=default_chat
    )
