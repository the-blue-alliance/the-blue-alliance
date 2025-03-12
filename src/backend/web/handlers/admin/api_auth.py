import logging
import random
import string
from datetime import datetime
from typing import cast, Optional

from flask import abort, redirect, request, url_for
from google.appengine.ext import ndb
from werkzeug.wrappers import Response

from backend.common.consts.auth_type import AuthType, WRITE_TYPE_NAMES
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.web.profiled_render import render_template


def api_auth_add() -> Response:
    template_values = {
        "auth_id": "".join(
            random.choice(
                string.ascii_lowercase + string.ascii_uppercase + string.digits
            )
            for _ in range(16)
        ),
    }

    return render_template("admin/api_add_auth.html", template_values)


def api_auth_delete(auth_id: str) -> Response:
    auth = ApiAuthAccess.get_by_id(auth_id)
    if auth is None:
        abort(404)

    template_values = {"auth": auth}

    return render_template("admin/api_delete_auth.html", template_values)


def api_auth_delete_post(auth_id: str) -> Response:
    logging.warning(f"Deleting auth: {auth_id}")

    auth = ApiAuthAccess.get_by_id(auth_id)
    if auth is None:
        abort(404)

    auth.key.delete()

    return redirect(url_for("admin.api_auth_manage"))


def api_auth_edit(auth_id: str) -> Response:
    auth = ApiAuthAccess.get_by_id(auth_id)
    if auth is None:
        abort(404)

    template_values = {
        "auth": auth,
    }

    return render_template("admin/api_edit_auth.html", template_values)


def api_auth_edit_post(auth_id: str) -> Response:
    auth = ApiAuthAccess.get_by_id(auth_id)

    auth_types_enum = (
        [AuthType.READ_API]
        if auth and AuthType.READ_API in auth.auth_types_enum
        else []
    )
    if request.form.get("allow_edit_teams"):
        auth_types_enum.append(AuthType.EVENT_TEAMS)
    if request.form.get("allow_edit_matches"):
        auth_types_enum.append(AuthType.EVENT_MATCHES)
    if request.form.get("allow_edit_rankings"):
        auth_types_enum.append(AuthType.EVENT_RANKINGS)
    if request.form.get("allow_edit_alliances"):
        auth_types_enum.append(AuthType.EVENT_ALLIANCES)
    if request.form.get("allow_edit_awards"):
        auth_types_enum.append(AuthType.EVENT_AWARDS)
    if request.form.get("allow_edit_match_video"):
        auth_types_enum.append(AuthType.MATCH_VIDEO)
    if request.form.get("allow_edit_info"):
        auth_types_enum.append(AuthType.EVENT_INFO)
    if request.form.get("allow_edit_zebra_motionworks"):
        auth_types_enum.append(AuthType.ZEBRA_MOTIONWORKS)

    owner_email = request.form.get("owner", None)
    if owner_email:
        owner = Account.query(Account.email == owner_email).fetch()
        owner_key = owner[0].key if owner else None
    else:
        owner_key = None

    expiration_date = request.form.get("expiration", None)
    if expiration_date:
        expiration = datetime.strptime(expiration_date, "%Y-%m-%d")
    else:
        expiration = None

    event_list_str = request.form.get("event_list_str")
    if event_list_str:
        split_events = event_list_str.split(",")
        event_keys = [event_key.strip() for event_key in split_events]
    else:
        event_keys = []

    district_list_str = request.form.get("district_list_str")
    if district_list_str:
        split_districts = district_list_str.split(",")
        district_list = [
            ndb.Key(District, district_key.strip()) for district_key in split_districts
        ]
        district_events = Event.query(
            cast(ndb.KeyProperty, Event.district_key).IN(district_list)
        ).fetch(keys_only=True)
        event_keys.extend(k.string_id() for k in district_events)
    else:
        district_list = []

    event_list = [ndb.Key(Event, k) for k in sorted(set(event_keys))]

    all_official_events = False
    if request.form.get("all_official_events"):
        all_official_events = True

    if not auth:
        auth = ApiAuthAccess(
            id=auth_id,
            description=request.form.get("description", ""),
            owner=owner_key,
            expiration=expiration,
            allow_admin=True if request.form.get("allow_admin") else False,
            secret="".join(
                random.choice(
                    string.ascii_lowercase + string.ascii_uppercase + string.digits
                )
                for _ in range(64)
            ),
            district_list=district_list,
            event_list=event_list,
            all_official_events=all_official_events,
            auth_types_enum=auth_types_enum,
        )
    else:
        auth.description = request.form.get("description", "")
        auth.event_list = event_list
        auth.district_list = district_list
        auth.all_official_events = all_official_events
        auth.auth_types_enum = auth_types_enum
        auth.owner = owner_key
        auth.expiration = expiration
        auth.allow_admin = True if request.form.get("allow_admin") else False

    auth.put()

    return redirect(url_for("admin.api_auth_manage"))


def api_auth_manage(key_type: Optional[str]) -> Response:
    if key_type == "write":
        auth_filter = cast(ndb.IntegerProperty, ApiAuthAccess.auth_types_enum).IN(
            list(WRITE_TYPE_NAMES.keys())
        )
    elif key_type == "read":
        auth_filter = ApiAuthAccess.auth_types_enum == AuthType.READ_API
    elif key_type == "admin":
        auth_filter = ndb.OR(
            ApiAuthAccess.allow_admin == True,  # noqa: E712
            ApiAuthAccess.all_official_events == True,  # noqa: E712
        )
    else:
        return redirect(url_for("admin.api_auth_manage", key_type="write"))

    include_expired = request.args.get("include_expired") == "true"
    if not include_expired:
        now: datetime = datetime.now()
        auth_query = ApiAuthAccess.query(
            ndb.AND(
                auth_filter,
                ndb.OR(
                    ApiAuthAccess.expiration == None,  # noqa: E711
                    ApiAuthAccess.expiration > now,  # noqa: E711
                ),
            )
        )
    else:
        auth_query = ApiAuthAccess.query(auth_filter)

    auths = auth_query.fetch()
    template_values = {
        "key_type": key_type,
        "include_expired": include_expired,
        "auths": auths,
    }

    return render_template("admin/api_manage_auth.html", template_values)
