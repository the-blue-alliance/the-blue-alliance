import datetime

from flask import redirect, request, url_for
from werkzeug.wrappers import Response

from backend.common.consts.auth_type import ADMIN_SKIP_TYPES, AuthType, WRITE_TYPE_NAMES
from backend.common.sitevars.apistatus import (
    AndroidConfig as TAndroidConfig,
    ApiStatus,
    ContentType as TApiStatus,
    IOSConfig as TIOSConfig,
)
from backend.common.sitevars.trusted_api import (
    ContentType as TTrustedApiConfig,
    TrustedApiConfig,
)
from backend.web.profiled_render import render_template


def apistatus_get() -> str:
    status = ApiStatus.get()
    trusted_sitevar = TrustedApiConfig.get()

    android_status = status["android"] or TAndroidConfig(
        latest_app_version=-1, min_app_version=-1
    )
    ios_status = status["ios"] or TIOSConfig(latest_app_version=-1, min_app_version=-1)

    template_values = {
        "max_year": status["max_season"],
        "current_year": status["current_season"],
        "android_latest_version": android_status["latest_app_version"],
        "android_min_version": android_status["min_app_version"],
        "ios_latest_version": ios_status["latest_app_version"],
        "ios_min_version": ios_status["min_app_version"],
        "enable_trustedapi": trusted_sitevar,
        "auth_types": set(AuthType) - ADMIN_SKIP_TYPES,
        "auth_type_names": WRITE_TYPE_NAMES,
    }

    return render_template("admin/apistatus.html", template_values)


def apistatus_post() -> Response:
    current_year = datetime.datetime.now().year
    status: TApiStatus = {
        "android": {
            "latest_app_version": int(request.form.get("android_latest_version", -1)),
            "min_app_version": int(request.form.get("android_min_version", -1)),
        },
        "ios": {
            "latest_app_version": int(request.form.get("ios_latest_version", -1)),
            "min_app_version": int(request.form.get("ios_min_version", -1)),
        },
        "max_season": int(request.form.get("max_year", current_year)),
        "current_season": int(request.form.get("current_year", current_year)),
    }
    ApiStatus.put(status)

    trusted_status: TTrustedApiConfig = {
        str(auth_type): bool(request.form.get(f"enable_{auth_type.name.lower()}"))
        for auth_type in set(AuthType) - ADMIN_SKIP_TYPES
    }
    TrustedApiConfig.put(trusted_status)

    return redirect(url_for("admin.apistatus_get"))
