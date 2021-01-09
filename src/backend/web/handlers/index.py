from backend.common.decorators import cached_public
from backend.common.helpers.season_helper import SeasonHelper
from backend.web.profiled_render import render_template


@cached_public
def index() -> str:
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
