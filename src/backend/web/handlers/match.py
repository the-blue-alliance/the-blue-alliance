import json
from datetime import timedelta
from typing import List, Optional

from flask import abort
from werkzeug.wrappers import Response

from backend.common.consts.alliance_color import AllianceColor
from backend.common.decorators import cached_public
from backend.common.flask_cache import make_cached_response
from backend.common.models.event import Event
from backend.common.models.keys import MatchKey
from backend.common.models.match import Match
from backend.common.models.zebra_motionworks import ZebraMotionWorks
from backend.web.profiled_render import render_template


def _format_team_list(team_keys: List[str]) -> str:
    """Format team keys like ['frc254', 'frc971B'] into '254, 971B'."""
    return ", ".join(key.replace("frc", "") for key in team_keys)


def _build_match_meta_description(match: Match, event: Event) -> str:
    """
    Build a meta description for a match page based on match status.

    Examples:
    - Played: "Teams 254, 971 beat 433, 1114 with a score of 125 to 120 in Quals 1
              at the 2024 Event Name in Location. Match results and videos."
    - Scheduled: "Teams 254, 971 vs 433, 1114 in Quals 1
                 at the 2024 Event Name in Location."
    - Unscheduled: "Quals 1 at the 2024 Event Name FIRST Robotics Competition
                   in Location."
    """
    red_teams = match.alliances.get(AllianceColor.RED, {}).get("teams", [])
    blue_teams = match.alliances.get(AllianceColor.BLUE, {}).get("teams", [])
    event_suffix = f"at the {event.year} {event.name} in {event.location}."

    # No teams assigned yet
    if not red_teams:
        return (
            f"{match.verbose_name} at the {event.year} {event.name} "
            f"FIRST Robotics Competition in {event.location}."
        )

    red_str = _format_team_list(red_teams)
    blue_str = _format_team_list(blue_teams)

    if match.has_been_played:
        red_score = match.alliances[AllianceColor.RED]["score"]
        blue_score = match.alliances[AllianceColor.BLUE]["score"]
        winner = match.winning_alliance

        if winner == AllianceColor.RED:
            result = (
                f"Teams {red_str} beat {blue_str} "
                f"with a score of {red_score} to {blue_score}"
            )
        elif winner == AllianceColor.BLUE:
            result = (
                f"Teams {blue_str} beat {red_str} "
                f"with a score of {blue_score} to {red_score}"
            )
        else:
            # Tie - put red first
            result = (
                f"Teams {red_str} tied {blue_str} "
                f"with a score of {red_score} to {blue_score}"
            )
        return (
            f"{result} in {match.verbose_name} {event_suffix} "
            f"Match results and videos."
        )
    else:
        return f"Teams {red_str} vs {blue_str} in {match.verbose_name} {event_suffix}"


@cached_public
def match_detail(match_key: MatchKey) -> Response:
    if not Match.validate_key_name(match_key):
        abort(404)

    match_future = Match.get_by_id_async(match_key)
    event_future = Event.get_by_id_async(match_key.split("_")[0])
    match: Optional[Match] = match_future.get_result()
    event: Optional[Event] = event_future.get_result()

    if not match or not event:
        abort(404)

    zebra_data = ZebraMotionWorks.get_by_id(match_key)
    """
    gdcv_data = MatchGdcvDataQuery(match_key).fetch()
    timeseries_data = None
    if gdcv_data and len(gdcv_data) >= 147 and len(gdcv_data) <= 150:  # Santiy checks on data
        timeseries_data = json.dumps(gdcv_data)
    """

    match_breakdown_template = None
    if match.score_breakdown is not None and match.year >= 2015:
        game_year = 2020 if match.year == 2021 else match.year
        match_breakdown_template = (
            "match_partials/match_breakdown/match_breakdown_{}.html".format(game_year)
        )

    template_values = {
        "event": event,
        "match": match,
        "match_breakdown_template": match_breakdown_template,
        "meta_description": _build_match_meta_description(match, event),
        "timeseries_data": None,  # timeseries_data,
        "zebra_data": json.dumps(zebra_data.data) if zebra_data else None,
    }

    return make_cached_response(
        render_template("match_details.html", template_values),
        ttl=timedelta(seconds=61) if event.within_a_day else timedelta(days=1),
    )
