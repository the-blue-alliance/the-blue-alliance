from flask import Blueprint
from flask_cors import CORS

from backend.api.handlers.district import (
    dcmp_history,
    district_advancement,
    district_awards,
    district_events,
    district_history,
    district_insights,
    district_list_year,
    district_rankings,
    district_teams,
)
from backend.api.handlers.event import (
    event,
    event_advancement_points,
    event_awards,
    event_detail,
    event_list_all,
    event_list_year,
    event_matches,
    event_playoff_advancement,
    event_teams,
    event_teams_media,
    event_teams_statuses,
)
from backend.api.handlers.insights import (
    insights_leaderboards_year,
    insights_notables_year,
)
from backend.api.handlers.match import match, zebra_motionworks
from backend.api.handlers.media import media_tags
from backend.api.handlers.regional_advancement import (
    regional_advancement,
    regional_rankings,
)
from backend.api.handlers.search import search_index
from backend.api.handlers.status import status
from backend.api.handlers.team import (
    team,
    team_awards,
    team_event_awards,
    team_event_matches,
    team_event_status,
    team_events,
    team_events_statuses_year,
    team_history,
    team_history_districts,
    team_history_robots,
    team_list,
    team_list_all,
    team_matches,
    team_media_tag,
    team_media_year,
    team_social_media,
    team_years_participated,
)

api_v3 = Blueprint("apiv3", __name__, url_prefix="/api/v3")
CORS(
    api_v3,
    origins="*",
    methods=["OPTIONS", "GET"],
    allow_headers=["X-TBA-Auth-Key", "If-None-Match", "If-Modified-Since"],
    expose_headers=["ETag"],
    max_age=24 * 60 * 60,
)

# Overall Status
api_v3.add_url_rule("/status", view_func=status)

# District
api_v3.add_url_rule(
    "/district/<string:district_abbreviation>/history", view_func=district_history
)
api_v3.add_url_rule("/district/<string:district_key>/awards", view_func=district_awards)
api_v3.add_url_rule("/district/<string:district_key>/events", view_func=district_events)
api_v3.add_url_rule(
    "/district/<string:district_key>/events/<model_type:model_type>",
    view_func=district_events,
)
api_v3.add_url_rule("/district/<string:district_key>/teams", view_func=district_teams)
api_v3.add_url_rule(
    "/district/<string:district_key>/teams/<model_type:model_type>",
    view_func=district_teams,
)
api_v3.add_url_rule(
    "/district/<string:district_key>/rankings", view_func=district_rankings
)
api_v3.add_url_rule(
    "/district/<string:district_key>/advancement", view_func=district_advancement
)
api_v3.add_url_rule(
    "/district/<string:district_abbreviation>/dcmp_history",
    view_func=dcmp_history,
)
api_v3.add_url_rule(
    "/district/<string:district_abbreviation>/insights",
    view_func=district_insights,
)

# District List
api_v3.add_url_rule("/districts/<int:year>", view_func=district_list_year)

# Event
api_v3.add_url_rule("/event/<string:event_key>", view_func=event)
api_v3.add_url_rule(
    "/event/<string:event_key>/<simple_model_type:model_type>", view_func=event
)
api_v3.add_url_rule(
    "/event/<string:event_key>/<event_detail_type:detail_type>",
    view_func=event_detail,
)
api_v3.add_url_rule(
    "/event/<string:event_key>/advancement_points",
    view_func=event_advancement_points,
)
api_v3.add_url_rule("/event/<string:event_key>/teams", view_func=event_teams)
api_v3.add_url_rule(
    "/event/<string:event_key>/teams/<model_type:model_type>",
    view_func=event_teams,
)
api_v3.add_url_rule(
    "/event/<string:event_key>/teams/statuses", view_func=event_teams_statuses
)

api_v3.add_url_rule("event/<string:event_key>/matches", view_func=event_matches)
# api_v3.add_url_rule("event/<string:event_key>/matches/timeseries", view_func=TODO)
api_v3.add_url_rule(
    "/event/<string:event_key>/matches/<model_type:model_type>",
    view_func=event_matches,
)
api_v3.add_url_rule("/event/<string:event_key>/awards", view_func=event_awards)
api_v3.add_url_rule(
    "/event/<string:event_key>/playoff_advancement", view_func=event_playoff_advancement
)
api_v3.add_url_rule("/event/<string:event_key>/team_media", view_func=event_teams_media)

# Event List
api_v3.add_url_rule("/events/all", view_func=event_list_all)
api_v3.add_url_rule("/events/all/<model_type:model_type>", view_func=event_list_all)
api_v3.add_url_rule("/events/<int:year>", view_func=event_list_year)
api_v3.add_url_rule(
    "/events/<int:year>/<model_type:model_type>", view_func=event_list_year
)

# Match
api_v3.add_url_rule("/match/<string:match_key>", view_func=match)
api_v3.add_url_rule(
    "/match/<string:match_key>/<simple_model_type:model_type>", view_func=match
)
# api_v3.add_url_rule("/match/<string:match_key>/timeseries", view_func=TODO)
api_v3.add_url_rule(
    "/match/<string:match_key>/zebra_motionworks", view_func=zebra_motionworks
)

# Media
api_v3.add_url_rule("/media/tags", view_func=media_tags)

# Team
api_v3.add_url_rule("/team/<string:team_key>", view_func=team)
api_v3.add_url_rule(
    "/team/<string:team_key>/<simple_model_type:model_type>", view_func=team
)

# Regional Advancement
api_v3.add_url_rule("/regional_advancement/<int:year>/", view_func=regional_advancement)
api_v3.add_url_rule(
    "/regional_advancement/<int:year>/rankings", view_func=regional_rankings
)

# Team History
api_v3.add_url_rule("/team/<string:team_key>/history", view_func=team_history)
api_v3.add_url_rule(
    "/team/<string:team_key>/years_participated", view_func=team_years_participated
)
api_v3.add_url_rule(
    "/team/<string:team_key>/districts", view_func=team_history_districts
)
api_v3.add_url_rule("/team/<string:team_key>/robots", view_func=team_history_robots)
api_v3.add_url_rule("/team/<string:team_key>/social_media", view_func=team_social_media)

# Team Events
api_v3.add_url_rule("/team/<string:team_key>/events", view_func=team_events)
api_v3.add_url_rule(
    "/team/<string:team_key>/events/<model_type:model_type>", view_func=team_events
)
api_v3.add_url_rule("/team/<string:team_key>/events/<int:year>", view_func=team_events)
api_v3.add_url_rule(
    "/team/<string:team_key>/events/<int:year>/<model_type:model_type>",
    view_func=team_events,
)
api_v3.add_url_rule(
    "/team/<string:team_key>/events/<int:year>/statuses",
    view_func=team_events_statuses_year,
)

# Team @ Event
api_v3.add_url_rule(
    "/team/<string:team_key>/event/<string:event_key>/matches",
    view_func=team_event_matches,
)
api_v3.add_url_rule(
    "/team/<string:team_key>/event/<string:event_key>/matches/<model_type:model_type>",
    view_func=team_event_matches,
)
api_v3.add_url_rule(
    "/team/<string:team_key>/event/<string:event_key>/awards",
    view_func=team_event_awards,
)
api_v3.add_url_rule(
    "/team/<string:team_key>/event/<string:event_key>/status",
    view_func=team_event_status,
)

# Team Awards
api_v3.add_url_rule("/team/<string:team_key>/awards", view_func=team_awards)
api_v3.add_url_rule("/team/<string:team_key>/awards/<int:year>", view_func=team_awards)

# Team Matches
api_v3.add_url_rule(
    "/team/<string:team_key>/matches/<int:year>", view_func=team_matches
)
api_v3.add_url_rule(
    "/team/<string:team_key>/matches/<int:year>/<model_type:model_type>",
    view_func=team_matches,
)

# Team Media
api_v3.add_url_rule(
    "/team/<string:team_key>/media/<int:year>", view_func=team_media_year
)
api_v3.add_url_rule(
    "/team/<string:team_key>/media/tag/<string:media_tag>", view_func=team_media_tag
)
api_v3.add_url_rule(
    "/team/<string:team_key>/media/tag/<string:media_tag>/<int:year>",
    view_func=team_media_tag,
)

# Team List
api_v3.add_url_rule("/teams/all", view_func=team_list_all)
api_v3.add_url_rule("/teams/all/<model_type:model_type>", view_func=team_list_all)
api_v3.add_url_rule("/teams/<int:page_num>", view_func=team_list)
api_v3.add_url_rule(
    "/teams/<int:page_num>/<model_type:model_type>", view_func=team_list
)
api_v3.add_url_rule("/teams/<int:year>/<int:page_num>", view_func=team_list)
api_v3.add_url_rule(
    "/teams/<int:year>/<int:page_num>/<model_type:model_type>",
    view_func=team_list,
)

# Insights
api_v3.add_url_rule(
    "/insights/leaderboards/<int:year>", view_func=insights_leaderboards_year
)
api_v3.add_url_rule("/insights/notables/<int:year>", view_func=insights_notables_year)

# Search
api_v3.add_url_rule("/search_index", view_func=search_index)
