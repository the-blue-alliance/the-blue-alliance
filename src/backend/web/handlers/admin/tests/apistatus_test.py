import datetime

from bs4 import BeautifulSoup
from werkzeug.test import Client

from backend.common.consts.auth_type import ADMIN_SKIP_TYPES, AuthType
from backend.common.sitevars.apistatus import ApiStatus
from backend.common.sitevars.trusted_api import TrustedApiConfig


def test_get_apistatus_defaults(
    ndb_context, login_gae_admin, web_client: Client
) -> None:
    resp = web_client.get("/admin/apistatus")
    assert resp.status_code == 200

    now_year = datetime.datetime.now().year
    soup = BeautifulSoup(resp.data, "html.parser")

    max_year = soup.find("input", {"name": "max_year"})
    assert max_year is not None
    assert max_year["value"] == f"{now_year}"

    current_year = soup.find("input", {"name": "current_year"})
    assert current_year is not None
    assert current_year["value"] == f"{now_year}"

    for auth_type in set(AuthType) - ADMIN_SKIP_TYPES:
        auth_checkbox = soup.find("input", {"name": f"enable_{auth_type.name.lower()}"})
        assert auth_checkbox is not None
        # By default, everything should be enabled
        assert (
            auth_checkbox.get("checked") is not None
        ), f"{auth_type.name} not enabled by default: {auth_checkbox}"


def test_get_apistatus_non_default(
    ndb_context, login_gae_admin, web_client: Client
) -> None:
    ApiStatus.put(
        {
            "android": {
                "latest_app_version": -1,
                "min_app_version": -1,
            },
            "ios": {
                "latest_app_version": -1,
                "min_app_version": -1,
            },
            "current_season": 2020,
            "max_season": 2020,
            "max_team_page": 1,
        }
    )
    TrustedApiConfig.put(
        {str(auth_type): False for auth_type in set(AuthType) - ADMIN_SKIP_TYPES}
    )

    resp = web_client.get("/admin/apistatus")
    assert resp.status_code == 200

    soup = BeautifulSoup(resp.data, "html.parser")

    max_year = soup.find("input", {"name": "max_year"})
    assert max_year is not None
    assert max_year["value"] == "2020"

    current_year = soup.find("input", {"name": "current_year"})
    assert current_year is not None
    assert current_year["value"] == "2020"

    for auth_type in set(AuthType) - ADMIN_SKIP_TYPES:
        auth_checkbox = soup.find("input", {"name": f"enable_{auth_type.name.lower()}"})
        assert auth_checkbox is not None
        assert (
            auth_checkbox.get("checked") is None
        ), f"{auth_type.name} not disabled: {auth_checkbox}"


def test_update_apistatus(ndb_context, login_gae_admin, web_client: Client) -> None:
    form_data = {
        "current_year": 2020,
        "max_year": 2021,
    }
    resp = web_client.post("/admin/apistatus", data=form_data)
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/apistatus"

    apistatus = ApiStatus.get()
    assert apistatus["current_season"] == 2020
    assert apistatus["max_season"] == 2021


def test_update_trustedapi_status(
    ndb_context, login_gae_admin, web_client: Client
) -> None:
    form_data = {
        f"enable_{auth_type.name.lower()}": ""
        for auth_type in set(AuthType) - ADMIN_SKIP_TYPES
    }

    resp = web_client.post("/admin/apistatus", data=form_data)
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/apistatus"

    for auth_type in set(AuthType) - ADMIN_SKIP_TYPES:
        assert TrustedApiConfig.is_auth_enalbed({auth_type}) is False
