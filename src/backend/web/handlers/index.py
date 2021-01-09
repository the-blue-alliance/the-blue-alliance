from backend.common.decorators import cached_public
from backend.common.helpers.season_helper import SeasonHelper
from backend.web.profiled_render import render_template


@cached_public
def index() -> str:
    effective_season_year = SeasonHelper.effective_season_year()
    # special_webcasts = FirebasePusher.get_special_webcasts()
    template_values = {
        "seasonstart_datetime_utc": SeasonHelper.first_event_datetime_utc(effective_season_year),
        # "events": EventHelper.getWeekEvents(),
        # "any_webcast_online": any(w.get('status') == 'online' for w in special_webcasts),
        # "special_webcasts": special_webcasts,
        "manual_password": "!+Gam3^time#2021",  # TODO: Pull from Sitevar
        "game_name": "INFINITE RECHARGE at Home",
        "game_animation_youtube_id": "gmiYWTmFRVE",
    }
    return render_template("index/index_buildseason.html", template_values)


def index_kickoff() -> str:
    # "any_webcast_online": any(w.get('status') == 'online' for w in special_webcasts),
    # special_webcasts = FirebasePusher.get_special_webcasts()
    effective_season_year = SeasonHelper.effective_season_year()
    template_values = {
        "is_kickoff": SeasonHelper.is_kickoff_at_least_one_day_away(
            year=effective_season_year
        ),
        "kickoff_datetime_est": SeasonHelper.kickoff_datetime_est(
            effective_season_year
        ),
        "kickoff_datetime_utc": SeasonHelper.kickoff_datetime_utc(
            effective_season_year
        ),
    }
    return render_template("index/index_kickoff.html", template_values)


@cached_public
def about() -> str:
    return render_template("about.html")
