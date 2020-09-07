from flask import abort, Blueprint, redirect, request, url_for
from pyre_extensions import none_throws
from werkzeug.wrappers import Response

from backend.common.helpers.youtube_video_helper import YouTubeVideoHelper
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)
from backend.web.auth import current_user
from backend.web.handlers.decorators import require_login
from backend.web.profiled_render import render_template


blueprint = Blueprint("suggestions", __name__, url_prefix="/suggest")


@blueprint.route("/event/webcast")
@require_login
def suggest_webcast() -> str:
    event_key = request.args.get("event_key")
    if not event_key:
        abort(404)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    template_values = {
        "status": request.args.get("status"),
        "event": event,
    }
    return render_template("suggestions/suggest_event_webcast.html", template_values)


@blueprint.route("/event/webcast", methods=["POST"])
@require_login
def submit_webcast() -> Response:
    event_key = request.form.get("event_key")
    webcast_url = request.form.get("webcast_url")
    webcast_date = request.form.get("webcast_date")

    if not webcast_url:
        return redirect(
            url_for(".suggest_webcast", event_key=event_key, status="blank_webcast")
        )

    if " " in webcast_url:
        # This is an invalid url
        return redirect(
            url_for(".suggest_webcast", event_key=event_key, status="invalid_url")
        )

    if "thebluealliance" in webcast_url:
        # TBA doesn't host webcasts, so we can reject this outright
        return redirect(
            url_for(".suggest_webcast", event_key=event_key, status="invalid_url")
        )

    user = current_user()
    status = SuggestionCreator.createEventWebcastSuggestion(
        author_account_key=none_throws(none_throws(user).account_key),
        webcast_url=webcast_url,
        webcast_date=webcast_date,
        event_key=event_key,
    )

    return redirect(
        url_for(".suggest_webcast", event_key=event_key, status=status.value)
    )


@blueprint.route("/match/video")
@require_login
def suggest_match_video() -> str:
    match_key = request.args.get("match_key")
    if not match_key or not Match.validate_key_name(match_key):
        abort(404)

    match_future = Match.get_by_id_async(match_key)
    event_future = Event.get_by_id_async(match_key.split("_")[0])

    match = match_future.get_result()
    event = event_future.get_result()

    if not match or not event:
        abort(404)

    template_values = {
        "status": request.args.get("status"),
        "event": event,
        "match": match,
    }
    return render_template("suggestions/suggest_match_video.html", template_values)


@blueprint.route("/match/video", methods=["POST"])
@require_login
def submit_match_video() -> Response:
    match_key = request.form.get("match_key") or ""
    youtube_url = request.form.get("youtube_url") or ""
    youtube_id = YouTubeVideoHelper.parse_id_from_url(youtube_url)

    if not Match.validate_key_name(match_key) or Match.get_by_id(match_key) is None:
        abort(404)

    if not youtube_id:
        return redirect(
            url_for(".suggest_match_video", match_key=match_key, status="invalid_url")
        )

    user = current_user()
    status = SuggestionCreator.createMatchVideoYouTubeSuggestion(
        author_account_key=none_throws(none_throws(user).account_key),
        youtube_id=youtube_id,
        match_key=match_key,
    )

    return redirect(
        url_for(".suggest_match_video", match_key=match_key, status=status.value)
    )


@blueprint.route("/event/video")
@require_login
def suggest_match_video_playlist() -> Response:
    event_key = request.args.get("event_key") or ""

    if not Event.validate_key_name(event_key):
        abort(404)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    template_values = {"event": event, "num_added": request.args.get("num_added")}
    return render_template(
        "suggestions/suggest_match_video_playlist.html", template_values
    )


@blueprint.route("/event/video", methods=["POST"])
@require_login
def submit_match_video_playlist() -> Response:
    event_key = request.form.get("event_key") or ""

    if not Event.validate_key_name(event_key):
        abort(404)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    match_futures = Match.query(Match.event == event.key).fetch_async(keys_only=True)
    valid_match_keys = [match.id() for match in match_futures.get_result()]

    num_videos = int(request.form.get("num_videos", 0))
    suggestions_added = 0
    for i in range(0, num_videos):
        yt_id = request.form.get(f"video_id_{i}")
        match_partial = request.form.get(f"match_partial_{i}")
        if not yt_id or not match_partial:
            continue

        match_key = f"{event_key}_{match_partial}"
        if match_key not in valid_match_keys:
            continue

        user = current_user()
        status = SuggestionCreator.createMatchVideoYouTubeSuggestion(
            author_account_key=none_throws(none_throws(user).account_key),
            youtube_id=yt_id,
            match_key=match_key,
        )
        if status == SuggestionCreationStatus.SUCCESS:
            suggestions_added += 1

    return redirect(
        url_for(
            ".suggest_match_video_playlist",
            event_key=event_key,
            num_added=suggestions_added,
        )
    )
