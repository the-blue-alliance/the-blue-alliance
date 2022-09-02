import logging
import random
import string
from datetime import datetime

from flask import abort, redirect, request, url_for
from google.appengine.ext import ndb
from werkzeug.wrappers import Response

from backend.common.consts.auth_type import AuthType
from backend.common.models.account import Account
from backend.common.models.api_auth_access import ApiAuthAccess
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
        event_list = [ndb.Key(Event, event_key.strip()) for event_key in split_events]
    else:
        event_list = []

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
            event_list=event_list,
            auth_types_enum=auth_types_enum,
        )
    else:
        auth.description = request.form.get("description", "")
        auth.event_list = event_list
        auth.auth_types_enum = auth_types_enum
        auth.owner = owner_key
        auth.expiration = expiration
        auth.allow_admin = True if request.form.get("allow_admin") else False

    auth.put()

    return redirect(url_for("admin.api_auth_manage"))


def api_auth_manage() -> Response:
    auths = ApiAuthAccess.query().fetch()
    write_auths = filter(lambda auth: auth.is_write_key, auths)
    read_auths = filter(lambda auth: auth.is_read_key, auths)
    admin_auths = filter(lambda auth: auth.allow_admin, auths)

    template_values = {
        "write_auths": write_auths,
        "read_auths": read_auths,
        "admin_auths": admin_auths,
    }

    return render_template("admin/api_manage_auth.html", template_values)
