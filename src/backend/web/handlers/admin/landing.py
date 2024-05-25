from typing import cast, Dict, Union

from flask import redirect, request, url_for
from werkzeug.wrappers import Response

from backend.common.consts.landing_type import LANDING_TYPE_NAMES, LandingType
from backend.common.sitevars.landing_config import (
    ContentType as LandingConfigContentType,
    LandingConfig,
)
from backend.web.profiled_render import render_template


def landing_edit() -> Response:
    if request.method == "POST":
        return landing_edit_post()
    else:
        return landing_edit_get()


def landing_edit_get() -> Response:
    landing_config = LandingConfig.get()
    template_values = {
        "current_config": landing_config,
        "current_landing": LandingConfig.current_landing_type(),
        "landing_types": LANDING_TYPE_NAMES,
    }
    return render_template("admin/main_landing.html", template_values)


def landing_edit_post() -> Response:
    props = request.values

    # Handle our integer key
    new_props: Dict[str, Union[bool, int, str]] = {
        "current_landing": int(props.get("landing_type", int(LandingType.BUILDSEASON)))
    }

    # Manually check for the 3 boolean keys
    landing_config_booleans = [
        "build_handler_show_avatars",
        "build_handler_show_password",
        "build_handler_show_ri3d",
    ]
    for key in landing_config_booleans:
        new_props[key] = key in props

    landing_config = LandingConfig.get()
    for key in landing_config.keys():
        if key == "current_landing" or key in landing_config_booleans:
            continue

        val = props.get(key, "")
        new_props[key] = val

    LandingConfig.put(cast(LandingConfigContentType, new_props))

    return redirect(url_for("admin.landing_edit"))
