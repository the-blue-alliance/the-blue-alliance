import json
from datetime import datetime
from typing import List, Optional

from flask import abort, Blueprint, redirect, request, url_for
from google.appengine.ext import ndb
from werkzeug.wrappers import Response

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.event_webcast_adder import EventWebcastAdder
from backend.common.helpers.webcast_helper import WebcastParser
from backend.common.helpers.youtube_video_helper import YouTubeVideoHelper
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
from backend.common.models.webcast import Webcast
from backend.web.decorators import audit_post_mutation, require_permission
from backend.web.profiled_render import render_template

blueprint = Blueprint("webcast_mod", __name__, url_prefix="/mod")


def _get_event_or_404(event_key: EventKey) -> Event:
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)
    return event


def _parse_webcast_type_or_400(webcast_type_raw: Optional[str]) -> WebcastType:
    if not webcast_type_raw:
        raise ValueError("invalid_webcast_type")

    try:
        return WebcastType(webcast_type_raw)
    except ValueError:
        raise ValueError("invalid_webcast_type")

    raise AssertionError("unreachable")


def _parse_webcast_index_or_400(webcast_index_raw: Optional[str]) -> int:
    if not webcast_index_raw:
        raise ValueError("invalid_webcast_index")

    try:
        return int(webcast_index_raw) - 1
    except (TypeError, ValueError):
        raise ValueError("invalid_webcast_index")

    raise AssertionError("unreachable")


def _redirect_webcast_detail(
    event_key: EventKey, *, status: Optional[str] = None, anchor: str = "webcasts"
) -> Response:
    if status is not None:
        return redirect(
            url_for(
                "webcast_mod.webcast_detail",
                event_key=event_key,
                _anchor=anchor,
                status=status,
            )
        )

    return redirect(
        url_for(
            "webcast_mod.webcast_detail",
            event_key=event_key,
            _anchor=anchor,
        )
    )


def _get_webcasts_with_status(webcasts: List[Webcast]) -> List[Webcast]:
    webcast_list: List[Webcast] = []
    for webcast in webcasts:
        webcast_with_status = webcast.copy()
        cached_status = WebcastOnlineStatusMemcache(webcast).get()
        if cached_status is not None:
            webcast_with_status.update(cached_status)
        if "status" not in webcast_with_status:
            webcast_with_status["status"] = WebcastStatus.UNKNOWN
        webcast_list.append(webcast_with_status)
    return webcast_list


def _is_date_within_event_range(event: Event, webcast_date: str) -> bool:
    try:
        webcast_day = datetime.strptime(webcast_date, "%Y-%m-%d").date()
    except ValueError:
        return False

    if event.start_date is None or event.end_date is None:
        return False

    event_start_date = event.start_date.date()
    event_end_date = event.end_date.date()
    return event_start_date <= webcast_day <= event_end_date


def _parse_new_webcast() -> Optional[Webcast]:
    webcast_url = request.form.get("webcast_url", "").strip()
    if webcast_url:
        webcast = WebcastParser.webcast_dict_from_url(webcast_url).get_result()
        if webcast is None:
            return None
    else:
        webcast_channel = request.form.get("webcast_channel", "").strip()
        if not webcast_channel:
            raise ValueError("missing_webcast_channel")

        webcast_type = _parse_webcast_type_or_400(request.form.get("webcast_type"))

        webcast = Webcast(type=webcast_type, channel=webcast_channel)
        webcast_file = request.form.get("webcast_file", "").strip()
        if webcast_file:
            webcast["file"] = webcast_file

    if webcast["type"] == WebcastType.YOUTUBE and "date" not in webcast:
        scheduled_dates = YouTubeVideoHelper.get_scheduled_start_times(
            [webcast["channel"]]
        ).get_result()
        scheduled_date = scheduled_dates.get(webcast["channel"])
        if scheduled_date:
            webcast["date"] = scheduled_date

    webcast_date = request.form.get("webcast_date", "").strip()
    if webcast_date:
        webcast["date"] = webcast_date

    return webcast


@blueprint.route("/webcasts", methods=["GET"])
@require_permission(AccountPermission.REVIEW_MEDIA)
def webcast_list() -> str:
    events = EventHelper.events_within_a_day()
    event_rows = [
        {"event": event, "webcasts": _get_webcasts_with_status(event.webcast or [])}
        for event in events
    ]
    return render_template("mod/webcast_list.html", {"event_rows": event_rows})


@blueprint.route("/webcast/<event_key>", methods=["GET"])
@require_permission(AccountPermission.REVIEW_MEDIA)
def webcast_detail(event_key: EventKey) -> str:
    event = _get_event_or_404(event_key)
    template_values = {
        "event": event,
        "webcasts": _get_webcasts_with_status(event.webcast or []),
    }
    return render_template("mod/webcast_detail.html", template_values)


@blueprint.route("/webcast/<event_key>/add", methods=["POST"])
@require_permission(AccountPermission.REVIEW_MEDIA)
@audit_post_mutation(target_key_getter=lambda event_key: ndb.Key(Event, event_key))
def webcast_add(event_key: EventKey) -> Response:
    event = _get_event_or_404(event_key)
    try:
        webcast = _parse_new_webcast()
    except ValueError as exc:
        return _redirect_webcast_detail(
            event.key_name,
            status=str(exc),
            anchor="add-webcast",
        )

    if webcast is None:
        return _redirect_webcast_detail(
            event.key_name,
            status="invalid_webcast_url",
            anchor="add-webcast",
        )

    EventWebcastAdder.add_webcast(event, webcast)

    return _redirect_webcast_detail(event.key_name, anchor="webcasts")


@blueprint.route("/webcast/<event_key>/remove", methods=["POST"])
@require_permission(AccountPermission.REVIEW_MEDIA)
@audit_post_mutation(target_key_getter=lambda event_key: ndb.Key(Event, event_key))
def webcast_remove(event_key: EventKey) -> Response:
    event = _get_event_or_404(event_key)

    webcast_channel = request.form.get("channel", "").strip()
    if not webcast_channel:
        return _redirect_webcast_detail(
            event.key_name,
            status="missing_webcast_channel",
            anchor="webcasts",
        )

    try:
        webcast_type = _parse_webcast_type_or_400(request.form.get("type"))
        webcast_index = _parse_webcast_index_or_400(request.form.get("index"))
    except ValueError as exc:
        return _redirect_webcast_detail(
            event.key_name,
            status=str(exc),
            anchor="webcasts",
        )

    webcast_file = request.form.get("file", "").strip() or None
    removed = EventWebcastAdder.remove_webcast(
        event, webcast_index, webcast_type, webcast_channel, webcast_file
    )
    if removed is None:
        return _redirect_webcast_detail(
            event.key_name,
            status="webcast_remove_mismatch",
            anchor="webcasts",
        )

    return _redirect_webcast_detail(event.key_name, anchor="webcasts")


@blueprint.route("/webcast/<event_key>/update_date", methods=["POST"])
@require_permission(AccountPermission.REVIEW_MEDIA)
@audit_post_mutation(target_key_getter=lambda event_key: ndb.Key(Event, event_key))
def webcast_update_date(event_key: EventKey) -> Response:
    event = _get_event_or_404(event_key)

    webcast_channel = request.form.get("channel", "").strip()
    if not webcast_channel:
        return _redirect_webcast_detail(
            event.key_name,
            status="missing_webcast_channel",
            anchor="webcasts",
        )

    try:
        webcast_type = _parse_webcast_type_or_400(request.form.get("type"))
        webcast_index = _parse_webcast_index_or_400(request.form.get("index"))
    except ValueError as exc:
        return _redirect_webcast_detail(
            event.key_name,
            status=str(exc),
            anchor="webcasts",
        )

    webcast_date = request.form.get("date", "").strip()

    if not webcast_date:
        return _redirect_webcast_detail(
            event.key_name,
            status="missing_webcast_date",
            anchor="webcasts",
        )

    try:
        datetime.strptime(webcast_date, "%Y-%m-%d")
    except ValueError:
        return _redirect_webcast_detail(
            event.key_name,
            status="invalid_webcast_date_format",
            anchor="webcasts",
        )

    if not _is_date_within_event_range(event, webcast_date):
        return _redirect_webcast_detail(
            event.key_name,
            status="webcast_date_out_of_range",
            anchor="webcasts",
        )

    webcasts = event.webcast
    if not webcasts or webcast_index >= len(webcasts):
        return _redirect_webcast_detail(
            event.key_name,
            status="invalid_webcast_index",
            anchor="webcasts",
        )

    webcast = webcasts[webcast_index]
    if webcast.get("type") != webcast_type or webcast.get("channel") != webcast_channel:
        return _redirect_webcast_detail(
            event.key_name,
            status="webcast_update_mismatch",
            anchor="webcasts",
        )

    webcast_file = request.form.get("file", "").strip()
    if webcast.get("file", "") != webcast_file:
        return _redirect_webcast_detail(
            event.key_name,
            status="webcast_update_mismatch",
            anchor="webcasts",
        )

    if webcast.get("date") != webcast_date:
        webcast["date"] = webcast_date
        event.webcast_json = json.dumps(webcasts)
        event._webcast = None
        event._dirty = True
        EventManipulator.createOrUpdate(event, auto_union=False)

    return _redirect_webcast_detail(event.key_name, anchor="webcasts")


@blueprint.route("/webcast/<event_key>/update_all_dates", methods=["POST"])
@require_permission(AccountPermission.REVIEW_MEDIA)
@audit_post_mutation(target_key_getter=lambda event_key: ndb.Key(Event, event_key))
def webcast_update_all_dates(event_key: EventKey) -> Response:
    event = _get_event_or_404(event_key)

    webcasts = event.webcast
    if not webcasts:
        return _redirect_webcast_detail(
            event.key_name,
            status="no_webcasts",
            anchor="webcasts",
        )

    youtube_video_ids = [
        webcast["channel"]
        for webcast in webcasts
        if webcast.get("type") == WebcastType.YOUTUBE and webcast.get("channel")
    ]
    if not youtube_video_ids:
        return _redirect_webcast_detail(
            event.key_name,
            status="no_youtube_webcasts",
            anchor="webcasts",
        )

    date_by_video_id = YouTubeVideoHelper.get_scheduled_start_times(
        youtube_video_ids
    ).get_result()

    changed = False
    for webcast in webcasts:
        if webcast.get("type") != WebcastType.YOUTUBE:
            continue
        video_id = webcast.get("channel")
        if not video_id:
            continue

        webcast_date = date_by_video_id.get(video_id)
        if webcast_date is None or not _is_date_within_event_range(event, webcast_date):
            continue

        if webcast.get("date") != webcast_date:
            webcast["date"] = webcast_date
            changed = True

    if changed:
        event.webcast_json = json.dumps(webcasts)
        event._webcast = None
        event._dirty = True
        EventManipulator.createOrUpdate(event, auto_union=False)

    return _redirect_webcast_detail(event.key_name, anchor="webcasts")
