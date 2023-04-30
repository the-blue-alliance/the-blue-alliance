from flask import redirect, request, url_for
from werkzeug import Response

from backend.common.consts.webcast_type import WebcastType
from backend.common.sitevars.gameday_special_webcasts import (
    GamedaySpecialWebcasts,
    WebcastType as TSpecialWebcast,
)
from backend.web.profiled_render import render_template


def gameday_dashboard() -> str:
    gd_sitevar = GamedaySpecialWebcasts.get()
    special_webcasts = gd_sitevar["webcasts"]
    path_aliases = gd_sitevar["aliases"]
    default_chat = gd_sitevar["default_chat"]

    template_values = {
        "webcasts": special_webcasts,
        "aliases": path_aliases,
        "default_chat": default_chat,
    }

    return render_template("/admin/gameday_dashboard.html", template_values)


def gameday_dashboard_post() -> Response:
    action = request.form["action"]
    item = request.form.get("item")

    if action == "add" and item == "webcast":
        webcast = TSpecialWebcast(
            type=WebcastType(request.form["webcast_type"]).value,
            channel=request.form["webcast_channel"],
            name=request.form["webcast_name"],
            key_name=request.form["webcast_urlkey"],
        )

        webcast_file = request.form.get("webcast_file")
        if webcast_file:
            webcast["file"] = webcast_file

        GamedaySpecialWebcasts.add_special_webcast(webcast)
    elif action == "delete" and item == "webcast":
        key_to_remove = request.form["webcast_key"]
        GamedaySpecialWebcasts.remove_special_webcast(key_to_remove)
    elif action == "add" and item == "alias":
        alias_name = request.form["alias_name"]
        alias_args = request.form["alias_args"]
        GamedaySpecialWebcasts.add_alias(alias_name, alias_args)
    elif action == "delete" and item == "alias":
        alias_name = request.form["alias_key"]
        GamedaySpecialWebcasts.remove_alias(alias_name)
    elif action == "defaultChat":
        new_channel = request.form["defaultChat"]
        GamedaySpecialWebcasts.set_default_chat(new_channel)

    return redirect(url_for("admin.gameday_dashboard"))
