from typing import Optional

from flask import abort, Blueprint, request
from google.appengine.ext import ndb

from backend.common.models.event import Event
from backend.common.models.keys import EventKey, MatchKey
from backend.common.models.match import Match
from backend.common.models.mobile_client import MobileClient
from backend.tasks_io.helpers.tbans_helper import TBANSHelper


blueprint = Blueprint("tbans", __name__, url_prefix="/tasks/tbans")


def _validate_event(event_key: EventKey) -> Event:
    if not Event.validate_key_name(event_key):
        abort(404)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    return event


def _validate_match(match_key: MatchKey) -> Match:
    if not Match.validate_key_name(match_key):
        abort(404)

    match = Match.get_by_id(match_key)
    if not match:
        abort(404)

    return match


def get_user_id() -> Optional[str]:
    user_id = None
    if request.method == "POST":
        user_id = request.form.get("user_id")
    return user_id


@blueprint.route("/alliance_selections/<string:event_key>", methods=["GET", "POST"])
def alliance_selections(event_key: EventKey) -> str:
    event = _validate_event(event_key)
    user_id = get_user_id()
    TBANSHelper.alliance_selection(event, user_id)
    return ""


@blueprint.route("/awards/<string:event_key>", methods=["GET", "POST"])
def awards(event_key: EventKey) -> str:
    event = _validate_event(event_key)
    user_id = get_user_id()
    TBANSHelper.awards(event, user_id)
    return ""


@blueprint.route("/event_level/<string:event_key>", methods=["GET", "POST"])
def event_level(match_key: MatchKey) -> str:
    match = _validate_match(match_key)
    user_id = get_user_id()
    TBANSHelper.event_level(match, user_id)
    return ""


@blueprint.route("/event_schedule/<string:event_key>", methods=["GET", "POST"])
def event_schedule(event_key: EventKey) -> str:
    event = _validate_event(event_key)
    user_id = get_user_id()
    TBANSHelper.event_schedule(event, user_id)
    return ""


@blueprint.route(
    "/schedule_upcoming_matches/<string:event_key>", methods=["GET", "POST"]
)
def schedule_upcoming_matches(event_key: EventKey) -> str:
    event = _validate_event(event_key)
    user_id = get_user_id()
    TBANSHelper.schedule_upcoming_matches(event, user_id)
    return ""


@blueprint.route("/match_score/<string:match_key>", methods=["GET", "POST"])
def match_score(match_key: MatchKey) -> str:
    match = _validate_match(match_key)
    user_id = get_user_id()
    TBANSHelper.alliance_selection(match, user_id)
    return ""


@blueprint.route("/match_upcoming/<string:match_key>", methods=["GET", "POST"])
def match_upcoming(match_key: MatchKey) -> str:
    match = _validate_match(match_key)
    user_id = get_user_id()
    TBANSHelper.match_upcoming(match, user_id)
    return ""


@blueprint.route("/match_video/<string:match_key>", methods=["GET", "POST"])
def match_video(match_key: MatchKey) -> str:
    match = _validate_match(match_key)
    user_id = get_user_id()
    TBANSHelper.alliance_selection(match, user_id)
    return ""


@blueprint.route("/ping", methods=["POST"])
def ping() -> str:
    user_id = get_user_id()
    if not user_id:
        abort(400)

    account = Account.get_by_id(user_id)
    if not account:
        abort(404)

    mobile_client_id = request.form.get("mobile_client_id")
    if not mobile_client_id:
        abort(404)

    client = MobileClient.get_by_id(int(mobile_client_id), parent=account.key)
    if client is None:
        abort(404)

    TBANSHelper.ping(client)
    return ""
