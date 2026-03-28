from typing import List, Optional

from flask import abort, Blueprint, redirect, request, url_for
from werkzeug.wrappers import Response

from backend.common.consts.account_permission import AccountPermission
from backend.common.consts.webcast_status import WebcastStatus
from backend.common.consts.webcast_type import WebcastType
from backend.common.helpers.event_webcast_adder import EventWebcastAdder
from backend.common.helpers.webcast_helper import WebcastParser
from backend.common.helpers.youtube_video_helper import YouTubeVideoHelper
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
from backend.common.models.webcast import Webcast
from backend.web.decorators import require_permission
from backend.web.profiled_render import render_template

blueprint = Blueprint("webcast_mod", __name__, url_prefix="/mod")


def _get_event_or_404(event_key: EventKey) -> Event:
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)
    return event


def _parse_webcast_type_or_400(webcast_type_raw: Optional[str]) -> WebcastType:
    if not webcast_type_raw:
        abort(400)

    try:
        return WebcastType(webcast_type_raw)
    except ValueError:
        abort(400)

    raise AssertionError("unreachable")


def _parse_webcast_index_or_400(webcast_index_raw: Optional[str]) -> int:
    if not webcast_index_raw:
        abort(400)

    try:
        return int(webcast_index_raw) - 1
    except (TypeError, ValueError):
        abort(400)

    raise AssertionError("unreachable")


def _copy_webcast(webcast: Webcast) -> Webcast:
    return webcast.copy()


def _get_webcasts_with_status(webcasts: List[Webcast]) -> List[Webcast]:
    webcast_list: List[Webcast] = []
    for webcast in webcasts:
        webcast_with_status = _copy_webcast(webcast)
        cached_status = WebcastOnlineStatusMemcache(webcast).get()
        if cached_status is not None:
            webcast_with_status.update(cached_status)
        if "status" not in webcast_with_status:
            webcast_with_status["status"] = WebcastStatus.UNKNOWN
        webcast_list.append(webcast_with_status)
    return webcast_list


def _get_active_events() -> List[Event]:
    events = Event.query().order(Event.start_date).fetch(500)
    return [event for event in events if event.within_a_day]


def _parse_new_webcast() -> Optional[Webcast]:
    webcast_url = request.form.get("webcast_url", "").strip()
    if webcast_url:
        webcast = WebcastParser.webcast_dict_from_url(webcast_url).get_result()
        if webcast is None:
            return None
    else:
        webcast_channel = request.form.get("webcast_channel", "").strip()
        if not webcast_channel:
            abort(400)

        webcast_type = _parse_webcast_type_or_400(request.form.get("webcast_type"))

        webcast = Webcast(type=webcast_type, channel=webcast_channel)
        webcast_file = request.form.get("webcast_file", "").strip()
        if webcast_file:
            webcast["file"] = webcast_file

    if webcast["type"] == WebcastType.YOUTUBE and "date" not in webcast:
        scheduled_date = YouTubeVideoHelper.get_scheduled_start_time(
            webcast["channel"]
        ).get_result()
        if scheduled_date:
            webcast["date"] = scheduled_date

    webcast_date = request.form.get("webcast_date", "").strip()
    if webcast_date:
        webcast["date"] = webcast_date

    return webcast


@blueprint.route("/webcasts", methods=["GET"])
@require_permission(AccountPermission.REVIEW_MEDIA)
def webcast_list() -> str:
    events = _get_active_events()
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
def webcast_add(event_key: EventKey) -> Response:
    event = _get_event_or_404(event_key)
    webcast = _parse_new_webcast()
    if webcast is None:
        return redirect(
            url_for(
                "webcast_mod.webcast_detail",
                event_key=event.key_name,
                webcast_url_error=1,
                _anchor="add-webcast",
            )
        )

    EventWebcastAdder.add_webcast(event, webcast)

    return redirect(
        url_for(
            "webcast_mod.webcast_detail", event_key=event.key_name, _anchor="webcasts"
        )
    )


@blueprint.route("/webcast/<event_key>/remove", methods=["POST"])
@require_permission(AccountPermission.REVIEW_MEDIA)
def webcast_remove(event_key: EventKey) -> Response:
    event = _get_event_or_404(event_key)

    webcast_channel = request.form.get("channel", "").strip()
    if not webcast_channel:
        abort(400)

    webcast_type = _parse_webcast_type_or_400(request.form.get("type"))
    webcast_index = _parse_webcast_index_or_400(request.form.get("index"))

    webcast_file = request.form.get("file", "").strip() or None
    EventWebcastAdder.remove_webcast(
        event, webcast_index, webcast_type, webcast_channel, webcast_file
    )

    return redirect(
        url_for(
            "webcast_mod.webcast_detail", event_key=event.key_name, _anchor="webcasts"
        )
    )
