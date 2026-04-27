import json
import logging
import random
import string
from typing import List

from flask import (
    abort,
    Blueprint,
    Flask,
    jsonify,
    make_response,
    redirect,
    request,
    url_for,
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.wrappers import Response

from backend.common.consts.auth_type import AuthType
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.event_type import EventType
from backend.common.environment import Environment
from backend.common.helpers.fms_companion_helper import FMSCompanionHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.memcache import MemcacheClient
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.models.match import Match
from backend.common.sitevars.apiv3_key import Apiv3Key
from backend.common.sitevars.nexus_api_secret import (
    ContentType as NexusApiSecretsContentType,
)
from backend.common.sitevars.nexus_api_secret import NexusApiSecrets
from backend.web.local.bootstrap import LocalDataBootstrap
from backend.web.local.dev_tools import (
    seed_media_suggestions,
    seed_test_event,
    seed_test_team,
)
from backend.web.profiled_render import render_template

"""
These are special handlers that only get installed when running locally
and are used as dev/unit test helpers
"""

DEV_AUTH_KEY = "tba-dev-key"

local_routes = Blueprint("local", __name__, url_prefix="/local")


@local_routes.before_request
def before_request() -> None:
    # Fail if we're not running in dev mode, as a sanity check
    if not Environment.is_dev():
        abort(403)


def ensure_dev_api_key() -> str:
    if not Environment.is_dev():
        raise RuntimeError("ensure_dev_api_key must only be called in dev mode")
    existing = ApiAuthAccess.get_by_id(DEV_AUTH_KEY)
    if not existing:
        ApiAuthAccess(
            id=DEV_AUTH_KEY,
            auth_types_enum=[AuthType.READ_API],
            description="Auto-created dev read API key",
        ).put()
    return DEV_AUTH_KEY


@local_routes.route("/bootstrap", methods=["GET"])
def bootstrap() -> str:
    dev_auth_key = ensure_dev_api_key()
    apiv3_key = Apiv3Key.api_key()
    template_values = {
        "apiv3_key": apiv3_key,
        "current_year": SeasonHelper.get_current_season(),
        "dev_auth_key": dev_auth_key,
        "nexus_api_key": NexusApiSecrets.auth_token() or "",
        "status": request.args.get("status"),
        "view_url": request.args.get("url"),
    }
    return render_template("local/bootstrap.html", template_values)


@local_routes.route("/bootstrap", methods=["POST"])
def bootstrap_post() -> Response:
    key = request.form.get("bootstrap_key", "")
    apiv3_key = request.form.get("apiv3_key") or Apiv3Key.api_key()

    if not apiv3_key:
        return redirect(url_for(".bootstrap", status="bad_apiv3"))

    return_url = LocalDataBootstrap.bootstrap_key(key, apiv3_key)
    return redirect(
        url_for(
            ".bootstrap",
            status="success" if return_url is not None else "bad_key",
            url=return_url,
        )
    )


@local_routes.route("/bootstrap/link_nexus_demo", methods=["POST"])
def bootstrap_link_nexus_demo_post() -> Response:
    test_event_key = (request.form.get("test_event_key") or "").strip().lower()
    if not test_event_key:
        test_event_key = f"{SeasonHelper.get_current_season()}test"
    nexus_demo_event_id = (request.form.get("nexus_demo_event_id") or "").strip()
    nexus_api_key = (request.form.get("nexus_api_key") or "").strip()
    should_save_api_key = bool(request.form.get("save_api_key"))

    if not Event.validate_key_name(test_event_key):
        return redirect(url_for(".bootstrap", status="bad_key"))

    event = Event.get_by_id(test_event_key)
    if not event:
        return redirect(url_for(".bootstrap", status="bad_key"))

    if not nexus_demo_event_id:
        return redirect(url_for(".bootstrap", status="bad_key"))

    event.nexus_code = nexus_demo_event_id
    EventManipulator.createOrUpdate(event)

    if should_save_api_key:
        NexusApiSecrets.put(NexusApiSecretsContentType(api_secret=nexus_api_key))

    return redirect(url_for(".bootstrap_nexus", event_key=test_event_key))


@local_routes.route("/bootstrap/nexus/<string:event_key>", methods=["GET"])
def bootstrap_nexus(event_key: str) -> str:
    if not Event.validate_key_name(event_key):
        abort(404)

    event = Event.get_by_id(event_key)
    if event is None:
        abort(404)

    eventteams = EventTeam.query(EventTeam.event == event.key).fetch()
    team_numbers: List[str] = sorted(
        [et.team.string_id().replace("frc", "") for et in eventteams],
        key=lambda team_number: int(team_number),
    )
    teams_text = "\n".join(team_numbers)

    matches = Match.query(
        Match.event == event.key,
        Match.comp_level == CompLevel.QM,
    ).fetch()
    matches = sorted(matches, key=lambda match: (match.set_number, match.match_number))

    matches_lines = []
    for match in matches:
        blue_teams = [
            team.replace("frc", "") for team in match.alliances["blue"]["teams"]
        ]
        red_teams = [
            team.replace("frc", "") for team in match.alliances["red"]["teams"]
        ]

        while len(blue_teams) < 3:
            blue_teams.append("")
        while len(red_teams) < 3:
            red_teams.append("")

        matches_lines.append(
            ",".join(
                [
                    "Qualification",
                    str(match.match_number),
                    blue_teams[0],
                    blue_teams[1],
                    blue_teams[2],
                    red_teams[0],
                    red_teams[1],
                    red_teams[2],
                ]
            )
        )
    matches_text = "\n".join(matches_lines)

    nexus_code = event.nexus_api_code

    template_values = {
        "event": event,
        "nexus_code": nexus_code,
        "team_import_url": f"https://frc.nexus/en/event/{nexus_code}/team-import",
        "match_import_url": f"https://frc.nexus/en/event/{nexus_code}/match-import",
        "teams_text": teams_text,
        "matches_text": matches_text,
    }
    return render_template("local/bootstrap_nexus.html", template_values)


@local_routes.route("/sdk_version")
def sdk_version() -> str:
    with open("/usr/lib/google-cloud-sdk/VERSION", "r") as version_file:
        return version_file.read()


@local_routes.route("/webhooks", methods=["POST"])
def webhook_server_post() -> str:
    incoming_webhook = request.json
    logging.info(f"got webhook: {incoming_webhook}")

    cache = MemcacheClient.get()
    cache.set(b"test_webhooks_received", json.dumps(incoming_webhook))

    return ""


@local_routes.route("/webhooks", methods=["GET"])
def webhook_server_get() -> Response:
    cache = MemcacheClient.get()
    webhooks = cache.get(b"test_webhooks_received") or "{}"
    cache.delete(b"test_webhooks_received")
    return jsonify(json.loads(webhooks))


@local_routes.route("/get_fms_companion_db/<string:event_key>", methods=["GET"])
def get_fms_companion_db(event_key: str) -> Response:
    file_contents = FMSCompanionHelper.read_newest_companion_db(event_key)
    if file_contents is None:
        return make_response(
            jsonify({"Error": f"No companion database found for event {event_key}"}),
            404,
        )

    response = make_response(file_contents)
    response.headers["Content-Type"] = "application/x-sqlite3"
    response.headers["Content-Disposition"] = (
        f"attachment; filename={f'{event_key}_companion.db'}"
    )
    return response


@local_routes.route("/create_test_event/<string:event_key>", methods=["POST"])
def create_test_event(event_key: str) -> Response:
    # Validate event key format
    if not Event.validate_key_name(event_key):
        return make_response(
            jsonify({"Error": "Invalid event key format."}),
            400,
        )

    # Parse event key to get year and event_short
    year_str = event_key[:4]
    year = int(year_str)
    event_short = event_key[4:]

    # Check if event already exists
    event = Event.get_by_id(event_key)
    if event:
        # Check if auth already exists
        existing_auth = ApiAuthAccess.query(ApiAuthAccess.event_list == event.key).get()
        if existing_auth:
            return jsonify(
                {
                    "Success": f"Event {event_key} already exists",
                    "event_key": event_key,
                    "auth_id": existing_auth.key.id(),
                    "auth_secret": existing_auth.secret,
                }
            )
    else:
        # Create new offseason event
        event = Event(
            id=event_key,
            year=year,
            event_short=event_short,
            event_type_enum=EventType.OFFSEASON,
            name=f"{year} {event_short.upper()} Test Event",
            short_name=f"{event_short.upper()} Test",
            official=False,
        )

        event = EventManipulator.createOrUpdate(event)

    # Generate auth credentials with all write permissions
    # Auth ID format: 16 character alphanumeric string
    auth_id = "".join(
        random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
        for _ in range(16)
    )
    # Auth secret format: 64 character alphanumeric string
    auth_secret = "".join(
        random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
        for _ in range(64)
    )

    # Get all write auth types (excluding READ_API)
    all_write_auth_types = [
        auth_type for auth_type in AuthType if auth_type != AuthType.READ_API
    ]

    auth = ApiAuthAccess(
        id=auth_id,
        secret=auth_secret,
        description=f"Auto-generated auth for test event {event_key}",
        event_list=[event.key],
        auth_types_enum=all_write_auth_types,
    )
    auth.put()

    return jsonify(
        {
            "Success": f"Event {event_key} created",
            "event_key": event_key,
            "auth_id": auth_id,
            "auth_secret": auth_secret,
        }
    )


@local_routes.route(
    "/seed_debug_mobile_clients/<string:account_id>", methods=["GET", "POST"]
)
def seed_debug_mobile_clients(account_id: str) -> Response:
    """Insert MobileClient rows whose `messaging_id` triggers each PingResult
    branch in `_ping_client` / `probe_and_cleanup_fcm_clients`. Hit this once
    in dev, then exercise the Connected Devices UI / admin probe button."""
    from google.appengine.ext import ndb

    from backend.common.consts.client_type import ClientType
    from backend.common.models.account import Account
    from backend.common.models.mobile_client import MobileClient

    parent_key = ndb.Key(Account, account_id)
    rows = [
        ("DEBUG_SENT_zach1", "Debug iPhone (sent)", ClientType.OS_IOS),
        ("DEBUG_FAILED_zach1", "Debug iPhone (failed)", ClientType.OS_IOS),
        ("DEBUG_DELETED_zach1", "Debug iPhone (deleted)", ClientType.OS_IOS),
        (
            "DEBUG_DELETED_zach2",
            "Debug Android (deleted)",
            ClientType.OS_ANDROID_FCM,
        ),
    ]
    created = []
    for messaging_id, name, ctype in rows:
        mc = MobileClient(
            parent=parent_key,
            user_id=account_id,
            messaging_id=messaging_id,
            client_type=ctype,
            device_uuid=f"uuid-{messaging_id}",
            display_name=name,
            verified=True,
        )
        mc.put()
        created.append({"messaging_id": messaging_id, "key_id": mc.key.id()})
    return jsonify({"account_id": account_id, "created": created})


local_routes.add_url_rule(
    "/seed_test_event",
    view_func=seed_test_event,
    methods=["POST"],
)

local_routes.add_url_rule(
    "/seed_test_team",
    view_func=seed_test_team,
    methods=["POST"],
)

local_routes.add_url_rule(
    "/seed_media_suggestions",
    view_func=seed_media_suggestions,
    methods=["POST"],
)


def maybe_register(app: Flask, csrf: CSRFProtect) -> None:
    if Environment.is_dev():
        app.register_blueprint(local_routes)

        from backend.common.deferred import install_defer_routes

        install_defer_routes(app)

        # Since we only install this on devservers, CSRF isn't necessary
        csrf.exempt(local_routes)
