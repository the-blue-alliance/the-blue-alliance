from werkzeug.test import Client

from backend.common.consts.landing_type import LandingType
from backend.common.sitevars.landing_config import LandingConfig


def test_landing_edit_get(web_client: Client, login_gae_admin) -> None:
    resp = web_client.get("/admin/main_landing")
    assert resp.status_code == 200


def test_landing_edit_post(web_client: Client, login_gae_admin) -> None:
    resp = web_client.post(
        "/admin/main_landing",
        data={
            "landing_type": str(int(LandingType.KICKOFF)),
            "build_handler_show_avatars": "on",
            "game_name": "Test Game",
        },
    )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/admin/main_landing"

    config = LandingConfig.get()
    assert config["current_landing"] == int(LandingType.KICKOFF)
    assert config["build_handler_show_avatars"] is True
    assert config["build_handler_show_password"] is False
    assert config["game_name"] == "Test Game"
    assert config["manual_password"] == ""
