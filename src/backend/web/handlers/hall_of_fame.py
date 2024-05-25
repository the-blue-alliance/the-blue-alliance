from collections import defaultdict
from datetime import timedelta

from werkzeug.wrappers import Response

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.consts.media_tag import MediaTag
from backend.common.decorators import cached_public
from backend.common.flask_cache import make_cached_response
from backend.common.models.award import Award
from backend.common.queries.media_query import TeamTagMediasQuery
from backend.web.profiled_render import render_template


@cached_public
def hall_of_fame_overview() -> Response:
    awards_future = Award.query(
        Award.award_type_enum == AwardType.CHAIRMANS,
        Award.event_type_enum == EventType.CMP_FINALS,
    ).fetch_async()

    teams_by_year = defaultdict(list)
    for award in awards_future.get_result():
        for team_key in award.team_list:
            teams_by_year[award.year].append(
                (
                    team_key.get_async(),
                    award.event.get_async(),
                    award,
                    TeamTagMediasQuery(
                        team_key.id(), MediaTag.CHAIRMANS_VIDEO
                    ).fetch_async(),
                    TeamTagMediasQuery(
                        team_key.id(), MediaTag.CHAIRMANS_PRESENTATION
                    ).fetch_async(),
                    TeamTagMediasQuery(
                        team_key.id(), MediaTag.CHAIRMANS_ESSAY
                    ).fetch_async(),
                )
            )

    teams_by_year = sorted(teams_by_year.items(), key=lambda k_v: -k_v[0])

    for _, team in teams_by_year:
        team.sort(key=lambda x: x[1].get_result().start_date)

    template_values = {
        "teams_by_year": teams_by_year,
    }

    return make_cached_response(
        render_template("hof.html", template_values),
        ttl=timedelta(weeks=1),
    )
