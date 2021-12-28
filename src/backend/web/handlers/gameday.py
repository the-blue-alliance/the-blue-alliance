import json
from datetime import datetime, timedelta

from flask import redirect, render_template

from backend.common.decorators import cached_public
from backend.common.models.event import Event
from backend.common.models.team import Team
from backend.common.queries.event_query import TeamYearEventsQuery
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


def get_param_string_for_event(event):
    current_webcasts = event.current_webcasts
    count = len(current_webcasts)
    if count == 0:
        return ""
    layout = count - 1 if count < 5 else 6  # Fall back to hex-view
    params = "#layout={}".format(layout)
    for i, webcast in enumerate(current_webcasts):
        # The various streams for an event are 0-indexed in GD2
        params += "&view_{0}={1}-{0}".format(i, event.key.id())
    return params


def gameday_redirect(alias):
    params = GamedaySpecialWebcasts.get_alias(alias)
    if params is not None:
        return redirect(f"/gameday{params}")

    # Allow an alias to be an event key
    if Event.validate_key_name(alias):
        event = Event.get_by_id(alias)
        if event:
            params = get_param_string_for_event(event)
            return redirect(f"/gameday{params}")

    # Allow an alias to be a team number
    team_key = "frc{}".format(alias)
    if Team.validate_key_name(team_key):
        now = datetime.now()
        team_events_future = TeamYearEventsQuery(
            team_key=team_key, year=now.year
        ).fetch_async()
        team_events = team_events_future.get_result()
        for event in team_events:
            # TODO: Handle more than the first event.
            # Should only matter for things like MICMP and CMP.
            if event and event.within_a_day:
                params = get_param_string_for_event(event)
                return redirect(f"/gameday{params}")

    # No matching alias. Redirect to GameDay.
    return redirect("/gameday")
