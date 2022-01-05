from flask import redirect, request, url_for
from werkzeug.wrappers import Response

from backend.common.sitevars.firebase_secrets import FirebaseSecrets
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.sitevars.gcm_server_key import GcmServerKey
from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.common.sitevars.livestream_secrets import LivestreamSecrets
from backend.common.sitevars.mobile_client_ids import MobileClientIds
from backend.common.sitevars.twitch_secrets import TwitchSecrets
from backend.web.profiled_render import render_template


def authkeys_get() -> str:
    google_secrets = GoogleApiSecret.get()
    firebase_secrets = FirebaseSecrets.get()
    gcm_serverKey = GcmServerKey.get()
    twitch_secrets = TwitchSecrets.get()
    livestream_secrets = LivestreamSecrets.get()
    fmsapi_keys = FMSApiSecrets.get()
    clientIds = MobileClientIds.get()

    template_values = {
        "google_secret": google_secrets.get("api_key", ""),
        "firebase_secret": firebase_secrets.get("FIREBASE_SECRET", ""),
        "fmsapi_user": fmsapi_keys.get("username", ""),
        "fmsapi_secret": fmsapi_keys.get("authkey", ""),
        "web_client_id": clientIds.get("web", ""),
        "android_client_id": clientIds.get("android", ""),
        "ios_client_id": clientIds.get("ios", ""),
        "gcm_key": gcm_serverKey.get("gcm_key", ""),
        "twitch_secret": twitch_secrets.get("client_id", ""),
        "livestream_secret": livestream_secrets.get("api_key", ""),
    }

    return render_template("admin/authkeys.html", template_values)


def authkeys_post() -> Response:
    google_key = request.form.get("google_secret")
    firebase_key = request.form.get("firebase_secret")
    fmsapi_user = request.form.get("fmsapi_user")
    fmsapi_secret = request.form.get("fmsapi_secret")
    web_client_id = request.form.get("web_client_id")
    android_client_id = request.form.get("android_client_id")
    ios_client_id = request.form.get("ios_client_id")
    gcm_key = request.form.get("gcm_key")
    twitch_client_id = request.form.get("twitch_secret")
    livestream_key = request.form.get("livestream_secret")

    GoogleApiSecret.put({"api_key": google_key})
    FirebaseSecrets.put({"FIREBASE_SECRET": firebase_key})
    FMSApiSecrets.put({"username": fmsapi_user, "authkey": fmsapi_secret})
    MobileClientIds.put(
        {
            "web": web_client_id,
            "android": android_client_id,
            "ios": ios_client_id,
        }
    )
    GcmServerKey.put({"gcm_key": gcm_key})

    twitch_secrets = TwitchSecrets.get()
    twitch_secrets["client_id"] = twitch_client_id
    TwitchSecrets.put(twitch_secrets)

    LivestreamSecrets.put({"api_key": livestream_key})

    return redirect(url_for("admin.authkeys_get"))
