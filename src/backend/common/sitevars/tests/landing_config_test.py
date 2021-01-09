import json

from backend.common.consts.landing_type import LandingType
from backend.common.models.sitevar import Sitevar
from backend.common.sitevars.landing_config import LandingConfig


def test_default_sitevar():
    default_sitevar = LandingConfig._fetch_sitevar()
    assert default_sitevar is not None

    default_json = {
        "kickoff_facebook_fbid": "",
        "game_teaser_youtube_id": "",
        "current_landing": 2,
        "game_animation_youtube_id": "",
        "game_name": "",
        "build_handler_show_avatars": False,
        "manual_password": "",
        "build_handler_show_password": False,
        "build_handler_show_ri3d": False,
    }
    assert default_sitevar.contents == default_json


def test_current_landing_type_default():
    assert LandingConfig.current_landing_type() == 2


def test_current_landing_type():
    Sitevar.get_or_insert(
        "landing_config",
        values_json=json.dumps({"current_landing": int(LandingType.OFFSEASON)}),
    )
    assert LandingConfig.current_landing_type() == LandingType.OFFSEASON
