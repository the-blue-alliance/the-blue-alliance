from werkzeug.test import Client

from backend.common.sitevars.firebase_secrets import FirebaseSecrets
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.sitevars.gcm_server_key import GcmServerKey
from backend.common.sitevars.google_api_secret import GoogleApiSecret
from backend.common.sitevars.livestream_secrets import LivestreamSecrets
from backend.common.sitevars.mobile_client_ids import MobileClientIds
from backend.common.sitevars.twitch_secrets import TwitchSecrets


def test_get_authkeys(login_gae_admin, web_client: Client) -> None:
    resp = web_client.get("/admin/authkeys")
    assert resp.status_code == 200


def test_update_authkeys(login_gae_admin, web_client: Client) -> None:
    data = {
        "google_secret": "google_secret",
        "firebase_secret": "firebase_secret",
        "fmsapi_user": "fmsapi_user",
        "fmsapi_secret": "fmsapi_secret",
        "web_client_id": "web_client_id",
        "android_client_id": "android_client_id",
        "ios_client_id": "ios_client_id",
        "gcm_key": "gcm_key",
        "twitch_client_id": "twitch_client_id",
        "twitch_secret": "twitch_secret",
        "livestream_secret": "livestream_secret",
    }
    resp = web_client.post("/admin/authkeys", data=data)
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/authkeys"

    google_secrets = GoogleApiSecret.get()
    firebase_secrets = FirebaseSecrets.get()
    gcm_serverKey = GcmServerKey.get()
    twitch_secrets = TwitchSecrets.get()
    livestream_secrets = LivestreamSecrets.get()
    fmsapi_keys = FMSApiSecrets.get()
    clientIds = MobileClientIds.get()

    check_data = {
        "google_secret": google_secrets.get("api_key", ""),
        "firebase_secret": firebase_secrets.get("FIREBASE_SECRET", ""),
        "fmsapi_user": fmsapi_keys.get("username", ""),
        "fmsapi_secret": fmsapi_keys.get("authkey", ""),
        "web_client_id": clientIds.get("web", ""),
        "android_client_id": clientIds.get("android", ""),
        "ios_client_id": clientIds.get("ios", ""),
        "gcm_key": gcm_serverKey.get("gcm_key", ""),
        "twitch_secret": twitch_secrets.get("client_secret", ""),
        "twitch_client_id": twitch_secrets.get("client_id", ""),
        "livestream_secret": livestream_secrets.get("api_key", ""),
    }
    assert data == check_data
