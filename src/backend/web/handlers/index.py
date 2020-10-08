from backend.common.decorators import cached_public
from backend.common.helpers.season_helper import SeasonHelper
from backend.web.profiled_render import render_template


@cached_public
def index() -> str:
    template_values = {
        "kickoff_datetime_est": SeasonHelper.kickoff_datetime_est(2021),
        "kickoff_datetime_utc": SeasonHelper.kickoff_datetime_utc(2021),
    }
    return render_template("index/index_kickoff.html", template_values)
