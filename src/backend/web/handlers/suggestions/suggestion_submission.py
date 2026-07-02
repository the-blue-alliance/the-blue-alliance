import re
from datetime import datetime
from urllib.parse import urlparse

from flask import abort, Blueprint, jsonify, redirect, request, url_for
from pyre_extensions import none_throws
from werkzeug.wrappers import Response

from backend.common.auth import current_user
from backend.common.consts.auth_type import WRITE_TYPE_NAMES
from backend.common.consts.media_type import MediaType
from backend.common.frc_api.frc_api import FRCAPI
from backend.common.helpers.media_helper import MediaHelper
from backend.common.helpers.website_helper import WebsiteHelper
from backend.common.helpers.youtube_video_helper import YouTubeVideoHelper
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.match import Match
from backend.common.models.team import Team
from backend.common.queries.media_query import (
    EventMediasQuery,
    TeamSocialMediaQuery,
    TeamYearMediaQuery,
)
from backend.common.suggestions.suggestion_creator import (
    SuggestionCreationStatus,
    SuggestionCreator,
)
from backend.web.decorators import enforce_login, require_login
from backend.web.profiled_render import render_template

blueprint = Blueprint("suggestions", __name__)

_FRC_EVENTS_URL_RE = re.compile(r"^/(\d{4})/([A-Za-z0-9]+)$")


def _parse_frc_events_link(frc_events_link: str) -> tuple[int, str] | None:
    parsed = urlparse(frc_events_link)
    if parsed.scheme != "https" or parsed.netloc != "frc-events.firstinspires.org":
        return None

    match = _FRC_EVENTS_URL_RE.match(parsed.path.rstrip("/"))
    if not match:
        return None

    year = int(match.group(1))
    event_code = match.group(2).upper()
    return year, event_code


def _normalized_event_name(event_name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", event_name.lower())


def _get_frc_event_code(
    frc_events_link: str,
    event_name: str,
    start_date: str,
    end_date: str,
) -> tuple[str | None, str | None]:
    link_parts = _parse_frc_events_link(frc_events_link)
    if link_parts is None:
        return (
            None,
            "Invalid frc-events link. Use a URL like https://frc-events.firstinspires.org/2026/INLAF",
        )

    year, event_code = link_parts

    try:
        response = FRCAPI().event_info(year, event_code).get_result()
    except Exception:
        return None, "Unable to validate frc-events link right now"

    if response.status_code != 200:
        return None, "Could not find this event on the FRC API"

    event_data = response.json() or {}
    events = event_data.get("Events") or []
    matched_event = next(
        (event for event in events if (event.get("code") or "").upper() == event_code),
        None,
    )
    if not matched_event:
        return None, "Could not find this event on the FRC API"

    frc_event_name = matched_event.get("name") or ""
    normalized_submitted_name = _normalized_event_name(event_name)
    normalized_frc_name = _normalized_event_name(frc_event_name)
    if (
        normalized_submitted_name
        and normalized_frc_name
        and normalized_submitted_name != normalized_frc_name
    ):
        return None, "frc-events link must point to the same event name"

    frc_start_date = (matched_event.get("dateStart") or "").split("T")[0]
    frc_end_date = (matched_event.get("dateEnd") or "").split("T")[0]
    if start_date and frc_start_date and start_date != frc_start_date:
        return None, "frc-events link must point to the same start date"
    if end_date and frc_end_date and end_date != frc_end_date:
        return None, "frc-events link must point to the same end date"

    try:
        if datetime.strptime(start_date, "%Y-%m-%d").year != year:
            return None, "frc-events link year must match the event year"
    except ValueError:
        pass

    return event_code, None


@blueprint.route("/suggest/event/webcast")
@require_login
def suggest_webcast() -> str:
    event_key = request.args.get("event_key")
    if not event_key:
        abort(404)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    uses_official_webcast_unit = False
    if event.event_district_key:
        district = District.get_by_id(event.event_district_key)
        if district:
            uses_official_webcast_unit = bool(district.uses_official_webcast_unit)

    template_values = {
        "status": request.args.get("status"),
        "event": event,
        "uses_official_webcast_unit": uses_official_webcast_unit,
    }
    return render_template("suggestions/suggest_event_webcast.html", template_values)


@blueprint.route("/suggest/event/webcast", methods=["POST"])
@require_login
def submit_webcast() -> Response:
    event_key = request.form.get("event_key", "")
    webcast_url = request.form.get("webcast_url", "")
    webcast_date = request.form.get("webcast_date", "")

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

    user = none_throws(current_user())
    status = SuggestionCreator.createEventWebcastSuggestion(
        author_account_key=none_throws(user.account_key),
        webcast_url=webcast_url,
        webcast_date=webcast_date,
        event_key=event_key,
    ).get_result()

    return redirect(
        url_for(".suggest_webcast", event_key=event_key, status=status.value)
    )


@blueprint.route("/suggest/match/video")
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


@blueprint.route("/suggest/match/video", methods=["POST"])
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

    user = none_throws(current_user())
    status = SuggestionCreator.createMatchVideoYouTubeSuggestion(
        author_account_key=none_throws(user.account_key),
        youtube_id=youtube_id,
        match_key=match_key,
    )

    return redirect(
        url_for(".suggest_match_video", match_key=match_key, status=status.value)
    )


@blueprint.route("/suggest/event/video")
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


@blueprint.route("/suggest/_/yt/playlist/videos")
@enforce_login
def resolve_youtube_playlist() -> Response:
    playlist_id = request.args.get("playlist_id")
    if not playlist_id:
        abort(400)

    playlist_videos = YouTubeVideoHelper.videos_in_playlist(playlist_id).get_result()
    return jsonify(playlist_videos)


@blueprint.route("/suggest/event/video", methods=["POST"])
@enforce_login
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

        user = none_throws(current_user())
        status = SuggestionCreator.createMatchVideoYouTubeSuggestion(
            author_account_key=none_throws(user.account_key),
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


@blueprint.route("/suggest/event/media")
@require_login
def suggest_event_media() -> Response:
    event_key = request.args.get("event_key", "")

    if not Event.validate_key_name(event_key):
        abort(404)

    event_future = Event.get_by_id_async(event_key)
    medias_future = EventMediasQuery(event_key).fetch_async()

    event = event_future.get_result()
    medias = medias_future.get_result()
    medias_by_slugname = MediaHelper.group_by_slugname(medias)

    if not event:
        abort(404)

    template_values = {
        "event": event,
        "status": request.args.get("status"),
        "medias_by_slugname": medias_by_slugname,
    }
    return render_template("suggestions/suggest_event_media.html", template_values)


@blueprint.route("/suggest/event/media", methods=["POST"])
@enforce_login
def submit_event_media() -> Response:
    event_key = request.form.get("event_key", "")

    if not Event.validate_key_name(event_key):
        abort(404)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    user = none_throws(current_user())
    status, suggestion = SuggestionCreator.createEventMediaSuggestion(
        author_account_key=none_throws(user.account_key),
        media_url=request.form.get("media_url", ""),
        event_key=event_key,
    ).get_result()

    return redirect(
        url_for(".suggest_event_media", event_key=event_key, status=status.value)
    )


@blueprint.route("/suggest/team/media")
@require_login
def suggest_team_media() -> Response:
    team_key = request.args.get("team_key", "")
    year_str = request.args.get("year", "")

    if not Team.validate_key_name(team_key) or not year_str.isdigit():
        abort(404)

    year = int(year_str)
    team = Team.get_by_id(team_key)
    if not team:
        abort(404)

    media_future = TeamYearMediaQuery(team_key=team.key_name, year=year).fetch_async()
    social_media_future = TeamSocialMediaQuery(team_key=team.key_name).fetch_async()

    medias = media_future.get_result()
    medias_by_slugname = MediaHelper.group_by_slugname(medias)

    social_medias = sorted(
        social_media_future.get_result(), key=MediaHelper.social_media_sorter
    )
    social_medias = filter(
        lambda m: m.media_type_enum == MediaType.INSTAGRAM_PROFILE, social_medias
    )  # we only allow IG media, so only show IG profile

    template_values = {
        "medias_by_slugname": medias_by_slugname,
        "social_medias": list(social_medias),
        "status": request.args.get("status"),
        "team": team,
        "year": year,
    }
    return render_template("suggestions/suggest_team_media.html", template_values)


@blueprint.route("/suggest/team/media", methods=["POST"])
@enforce_login
def submit_team_media() -> Response:
    team_key = request.form.get("team_key", "")
    year_str = request.form.get("year", "")
    if not Team.validate_key_name(team_key) or not year_str.isdigit():
        abort(404)

    team = Team.get_by_id(team_key)
    if not team:
        abort(404)

    user = none_throws(current_user())
    status, suggestion = SuggestionCreator.createTeamMediaSuggestion(
        author_account_key=none_throws(user.account_key),
        media_url=request.form.get("media_url", ""),
        team_key=team_key,
        year_str=year_str,
    ).get_result()
    return redirect(
        url_for(
            ".suggest_team_media", team_key=team_key, year=year_str, status=status.value
        )
    )


@blueprint.route("/suggest/team/social_media")
@require_login
def suggest_team_social_media() -> Response:
    team_key = request.args.get("team_key", "")

    if not Team.validate_key_name(team_key):
        abort(404)

    team = Team.get_by_id(team_key)
    if not team:
        abort(404)

    medias_future = TeamSocialMediaQuery(team_key=team_key).fetch_async()
    social_medias = medias_future.get_result()

    template_values = {
        "team": team,
        "status": request.args.get("status"),
        "social_medias": social_medias,
    }
    return render_template(
        "suggestions/suggest_team_social_media.html", template_values
    )


@blueprint.route("/suggest/team/social_media", methods=["POST"])
@enforce_login
def submit_team_social_media() -> Response:
    team_key = request.form.get("team_key", "")

    if not Team.validate_key_name(team_key):
        abort(404)

    team = Team.get_by_id(team_key)
    if not team:
        abort(404)

    user = none_throws(current_user())
    status, suggestion = SuggestionCreator.createTeamMediaSuggestion(
        author_account_key=none_throws(user.account_key),
        media_url=request.form.get("media_url", ""),
        team_key=team_key,
        year_str=None,
        is_social=True,
    ).get_result()
    return redirect(
        url_for(".suggest_team_social_media", team_key=team_key, status=status.value)
    )


@blueprint.route("/request/apiwrite")
@require_login
def request_apiwrite() -> Response:
    template_values = {
        "auth_types": WRITE_TYPE_NAMES,
        "status": request.args.get("status"),
    }
    return render_template("suggestions/suggest_apiwrite.html", template_values)


@blueprint.route("/request/apiwrite", methods=["POST"])
@enforce_login
def submit_apiwrite() -> Response:
    auth_types = request.form.getlist("auth_types", type=int)
    event_key = request.form.get("event_key", "")
    role = request.form.get("role", "")

    if not Event.validate_key_name(event_key):
        abort(404)

    user = none_throws(current_user())
    status = SuggestionCreator.createApiWriteSuggestion(
        author_account_key=none_throws(user.account_key),
        event_key=event_key,
        affiliation=role,
        auth_types=auth_types,
    )

    """
    # TODO support outgoing emails
    if status == SuggestionCreationStatus.SUCCESS:
            subject, body = self._gen_notification_email(event_key, self.user_bundle)
            OutgoingNotificationHelper.send_admin_alert_email(subject, body)
    """

    return redirect(url_for(".request_apiwrite", status=status.value))


@blueprint.route("/suggest/offseason")
@require_login
def suggest_offseason() -> Response:
    template_values = {
        "status": request.args.get("status"),
    }
    return render_template("suggestions/suggest_offseason_event.html", template_values)


@blueprint.route("/suggest/offseason", methods=["POST"])
@enforce_login
def submit_offseason() -> Response:
    user = none_throws(current_user())
    event_name = request.form.get("name", "")
    start_date = request.form.get("start_date", "")
    end_date = request.form.get("end_date", "")
    venue_name = (request.form.get("venue_name") or "").strip()
    venue_address = (request.form.get("venue_address") or "").strip()
    venue_city = (request.form.get("venue_city") or "").strip()
    venue_state = (request.form.get("venue_state") or "").strip()
    venue_country = (request.form.get("venue_country") or "").strip()
    frc_events_link = (request.form.get("frc_events_link") or "").strip() or None
    website = WebsiteHelper.format_url(request.form.get("website", None))

    first_code = None
    frc_events_link_error = None
    if frc_events_link:
        first_code, frc_events_link_error = _get_frc_event_code(
            frc_events_link,
            event_name,
            start_date,
            end_date,
        )

    failures = None
    if frc_events_link_error:
        status = SuggestionCreationStatus.VALIDATION_FAILURE
        failures = {"frc_events_link": frc_events_link_error}
    else:
        status, failures = SuggestionCreator.createOffseasonEventSuggestion(
            author_account_key=none_throws(user.account_key),
            name=event_name,
            start_date=start_date,
            end_date=end_date,
            website=website,
            venue_name=venue_name,
            address=venue_address,
            city=venue_city,
            state=venue_state,
            country=venue_country,
            first_code=first_code,
        )

    if status != "success":
        # Don't completely wipe form data if validation fails
        template_values = {
            "status": status,
            "failures": failures,
            "name": request.form.get("name", None),
            "start_date": request.form.get("start_date", None),
            "end_date": request.form.get("end_date", None),
            "website": request.form.get("website", None),
            "venue_name": request.form.get("venue_name", None),
            "venue_address": request.form.get("venue_address", None),
            "venue_city": request.form.get("venue_city", None),
            "venue_state": request.form.get("venue_state", None),
            "venue_country": request.form.get("venue_country", None),
            "frc_events_link": request.form.get("frc_events_link", None),
        }
        return render_template(
            "suggestions/suggest_offseason_event.html", template_values
        )
    else:
        # TODO support outgoing emails
        # subject, body = self._gen_notification_email(event_name)
        # OutgoingNotificationHelper.send_admin_alert_email(subject, body)
        return redirect(url_for(".suggest_offseason", status=status.value))
