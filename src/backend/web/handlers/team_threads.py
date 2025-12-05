import datetime

from flask import abort

from backend.common.consts.media_type import MediaType
from backend.common.decorators import cached_public
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.keys import Year
from backend.common.queries.media_query import MediaTypeYearQuery
from backend.web.profiled_render import render_template


@cached_public
def team_threads(year: Year) -> str:
    if year not in SeasonHelper.get_valid_years():
        abort(404)

    all_cd_threads = (
        MediaTypeYearQuery(MediaType.CD_THREAD, year).fetch_async().get_result()
    )

    rows = []
    for thread in all_cd_threads:
        rows.append(
            {
                "year": thread.year,
                "team_number": int(thread.references[0].id()[3:]),
                "thread_title": thread.details["thread_title"],
                "thread_url": thread.view_image_url,
            }
        )

    rows.sort(key=lambda x: x["team_number"])

    template_values = {
        "year": year,
        "rows": rows,
    }
    return render_template("team_threads.html", template_values)


@cached_public
def team_threads_canonical() -> str:
    current_year = datetime.datetime.now().year
    return team_threads(current_year)
