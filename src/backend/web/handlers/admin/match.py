import json

from flask import abort, redirect, request, url_for
from pyre_extensions import none_throws
from werkzeug.wrappers import Response

from backend.common.datafeed_parsers.csv_offseason_matches_parser import (
    CSVOffseasonMatchesParser,
)
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.models.event import Event
from backend.common.models.keys import MatchKey
from backend.common.models.match import Match
from backend.web.profiled_render import render_template


def match_dashboard() -> str:
    return render_template("admin/match_dashboard.html")


def match_detail(match_key: MatchKey) -> str:
    if not Match.validate_key_name(match_key):
        abort(404)

    match = Match.get_by_id(match_key)
    if not match:
        abort(404)

    template_values = {"match": match}
    return render_template("admin/match_details.html", template_values)


def match_edit(match_key: MatchKey) -> str:
    if not Match.validate_key_name(match_key):
        abort(404)

    match = Match.get_by_id(match_key)
    if not match:
        abort(404)

    template_values = {"match": match}
    return render_template("admin/match_edit.html", template_values)


def match_edit_post(match_key):
    alliances_json = request.form.get("alliances_json")
    score_breakdown_json = request.form.get("score_breakdown_json")
    # Ignore u'None' from form POST
    score_breakdown_json = (
        score_breakdown_json if score_breakdown_json != "None" else None
    )
    # Fake JSON load of the score breakdown to ensure the JSON is proper before attempting to save to the DB
    if score_breakdown_json:
        json.loads(score_breakdown_json)
    alliances = json.loads(alliances_json)
    tba_videos = (
        json.loads(request.form.get("tba_videos"))
        if request.form.get("tba_videos")
        else []
    )
    youtube_videos = (
        json.loads(request.form.get("youtube_videos"))
        if request.form.get("youtube_videos")
        else []
    )
    display_name = request.form.get("display_name")
    team_key_names = list()

    for alliance in alliances:
        team_key_names.extend(alliances[alliance].get("teams", None))

    match = Match(
        id=match_key,
        event=Event.get_by_id(request.form.get("event_key_name")).key,
        set_number=int(request.form.get("set_number")),
        match_number=int(request.form.get("match_number")),
        comp_level=request.form.get("comp_level"),
        team_key_names=team_key_names,
        alliances_json=alliances_json,
        score_breakdown_json=score_breakdown_json,
        tba_videos=tba_videos,
        youtube_videos=youtube_videos,
        no_auto_update=str(request.form.get("no_auto_update")).lower() == "true",
        display_name=display_name if display_name != "None" else None,
    )
    MatchManipulator.createOrUpdate(match, auto_union=False)

    return redirect(url_for("admin.match_detail", match_key=match.key_name))


def match_delete(match_key: MatchKey) -> str:
    if not Match.validate_key_name(match_key):
        abort(404)

    match = Match.get_by_id(match_key)
    if not match:
        abort(404)

    template_values = {"match": match}
    return render_template("admin/match_delete.html", template_values)


def match_delete_post(match_key: MatchKey) -> Response:
    if not Match.validate_key_name(match_key):
        abort(404)

    match = Match.get_by_id(match_key)
    if not match:
        abort(404)

    MatchManipulator.delete(match)

    return redirect(url_for("admin.event_detail", event_key=match.event.id()))


def match_add() -> Response:
    event_key = request.form.get("event_key")
    matches_csv = request.form.get("matches_csv")

    matches, _ = CSVOffseasonMatchesParser.parse(matches_csv)

    event = Event.get_by_id(none_throws(event_key))
    if not event:
        abort(404)

    matches = [
        Match(
            id=Match.render_key_name(
                event.key_name,
                match.get("comp_level", None),
                match.get("set_number", 0),
                match.get("match_number", 0),
            ),
            event=event.key,
            year=event.year,
            set_number=match.get("set_number", 0),
            match_number=match.get("match_number", 0),
            comp_level=match.get("comp_level", None),
            team_key_names=match.get("team_key_names", None),
            alliances_json=match.get("alliances_json", None),
        )
        for match in matches
    ]
    MatchManipulator.createOrUpdate(matches)

    return redirect(url_for("admin.event_detail", event_key=event_key))


def match_override_score_breakdown() -> Response:
    match_key = none_throws(request.form.get("match_key"))
    match = Match.get_by_id(match_key)
    if not match:
        abort(404)

    breakdown_json = none_throws(request.form.get("new_breakdown"))
    match.score_breakdown_json = json.dumps(json.loads(breakdown_json))
    MatchManipulator.createOrUpdate(match)

    return redirect(url_for("admin.event_detail", event_key=match.event_key_name))
