import collections
import json
import re
from typing import List, Optional

from flask import abort, redirect, request
from google.cloud import ndb
from pyre_extensions import none_throws, safe_cast
from werkzeug.wrappers import Response

from backend.common.consts import playoff_type
from backend.common.decorators import cached_public
from backend.common.helpers.award_helper import AwardHelper
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.media_helper import MediaHelper
from backend.common.helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.helpers.team_helper import TeamHelper
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, Year
from backend.common.models.team import Team
from backend.common.queries import district_query, event_query, media_query
from backend.web.profiled_render import render_template


@cached_public
def event_list(year: Optional[Year] = None) -> Response:
    explicit_year = year is not None
    if year is None:
        year = SeasonHelper.get_current_season()

    valid_years = SeasonHelper.get_valid_years()
    if year not in valid_years:
        abort(404)

    state_prov = request.args.get("state_prov", None)
    districts_future = district_query.DistrictsInYearQuery(year).fetch_async()
    all_events_future = event_query.EventListQuery(
        year
    ).fetch_async()  # Needed for state_prov
    if state_prov:
        events_future = Event.query(
            Event.year == year, Event.state_prov == state_prov
        ).fetch_async()
    else:
        events_future = all_events_future

    events = events_future.get_result()
    if state_prov == "" or (state_prov and not events):
        return redirect(request.path)

    EventHelper.sort_events(events)

    week_events = EventHelper.groupByWeek(events)

    districts = []  # a tuple of (district abbrev, district name)
    for district in districts_future.get_result():
        districts.append((district.abbreviation, district.display_name))
    districts = sorted(districts, key=lambda d: d[1])

    valid_state_provs = set()
    for event in all_events_future.get_result():
        if event.state_prov:
            valid_state_provs.add(event.state_prov)
    valid_state_provs = sorted(valid_state_provs)

    template_values = {
        "events": events,
        "explicit_year": explicit_year,
        "selected_year": year,
        "valid_years": valid_years,
        "week_events": week_events,
        "districts": districts,
        "state_prov": state_prov,
        "valid_state_provs": valid_state_provs,
    }
    return render_template("event_list.html", template_values)


@cached_public
def event_detail(event_key: EventKey) -> Response:
    event = event_query.EventQuery(event_key).fetch()

    if not event:
        abort(404)

    event = none_throws(event)  # for pyre
    event.prepAwardsMatchesTeams()
    event.prep_details()
    medias_future = media_query.EventTeamsPreferredMediasQuery(event_key).fetch_async()
    district_future = (
        district_query.DistrictQuery(none_throws(event.district_key).id()).fetch_async()
        if event.district_key
        else None
    )
    event_medias_future = media_query.EventMediasQuery(event_key).fetch_async()
    # status_sitevar_future = Sitevar.get_by_id_async('apistatus.down_events')

    event_divisions_future = None
    event_codivisions_future = None
    parent_event_future = None
    if event.divisions:
        event_divisions_future = ndb.get_multi_async(event.divisions)
    elif event.parent_event:
        parent_event_future = none_throws(event.parent_event).get_async()
        event_codivisions_future = event_query.EventDivisionsQuery(
            none_throws(event.parent_event).id()
        ).fetch_async()

    awards = AwardHelper.organizeAwards(event.awards)
    cleaned_matches = event.matches
    # MatchHelper.deleteInvalidMatches(event.matches, event)
    match_count, matches = MatchHelper.organizeMatches(cleaned_matches)
    teams = TeamHelper.sortTeams(safe_cast(List[Optional[Team]], event.teams))

    # Organize medias by team
    image_medias = MediaHelper.get_images(
        [media for media in medias_future.get_result()]
    )
    team_medias = collections.defaultdict(list)
    for image_media in image_medias:
        for reference in image_media.references:
            team_medias[reference].append(image_media)
    team_and_medias = []
    for team in teams:
        team_and_medias.append((team, team_medias.get(team.key, [])))

    num_teams = len(team_and_medias)
    middle_value = num_teams // 2
    if num_teams % 2 != 0:
        middle_value += 1
    teams_a, teams_b = team_and_medias[:middle_value], team_and_medias[middle_value:]

    num_matchstats = 15
    matchstats = collections.OrderedDict()
    if event.matchstats is not None:
        matchstats["OPRs"] = sorted(
            event.matchstats["oprs"].items(), key=lambda t: -t[1]
        )[:num_matchstats]
        matchstats["DPRs"] = sorted(
            event.matchstats["dprs"].items(), key=lambda t: -t[1]
        )[:num_matchstats]
        matchstats["CCWMs"] = sorted(
            event.matchstats["ccwms"].items(), key=lambda t: -t[1]
        )[:num_matchstats]

        if "coprs" in event.matchstats:
            for component, copr_dict in event.matchstats["coprs"].items():
                matchstats[component] = sorted(copr_dict.items(), key=lambda t: -t[1])[
                    :num_matchstats
                ]

    # Replace non-alphanumeric characters with underscores
    # in order to make sure that the html div IDs are valid
    matchstat_dropdown_id_map = {
        k: re.sub("[^0-9a-zA-Z]+", "_", k) for k in matchstats.keys()
    }

    if event.now:
        matches_recent = MatchHelper.recentMatches(cleaned_matches)
        matches_upcoming = MatchHelper.upcomingMatches(cleaned_matches)
    else:
        matches_recent = None
        matches_upcoming = None

    bracket_table = event.playoff_bracket
    playoff_advancement = event.playoff_advancement
    double_elim_matches = PlayoffAdvancementHelper.getDoubleElimMatches(event, matches)
    playoff_template = PlayoffAdvancementHelper.getPlayoffTemplate(event)

    # Lazy handle the case when we haven't backfilled the event details
    if not bracket_table or not playoff_advancement:
        (
            bracket_table2,
            playoff_advancement2,
            _,
            _,
        ) = PlayoffAdvancementHelper.generatePlayoffAdvancement(event, matches)
        bracket_table = bracket_table or bracket_table2
        playoff_advancement = playoff_advancement or playoff_advancement2

    district_points_sorted = None
    if event.district_key and event.district_points:
        district_points_sorted = sorted(
            none_throws(event.district_points)["points"].items(),
            key=lambda team_and_points: -team_and_points[1]["total"],
        )

    event_insights = event.details.insights if event.details else None
    event_insights_template = None
    if event_insights:
        event_insights_template = "event_partials/event_insights_{}.html".format(
            event.year
        )

    district = district_future.get_result() if district_future else None
    event_divisions = None
    if event_divisions_future:
        event_divisions = [e.get_result() for e in event_divisions_future]
    elif event_codivisions_future:
        event_divisions = event_codivisions_future.get_result()

    medias_by_slugname = MediaHelper.group_by_slugname(
        [media for media in event_medias_future.get_result()]
    )
    has_time_predictions = matches_upcoming and any(
        match.predicted_time for match in matches_upcoming
    )

    # status_sitevar = status_sitevar_future.get_result()

    template_values = {
        "event": event,
        "event_down": False,  # status_sitevar and event_key in status_sitevar.contents,
        "district_name": district.display_name if district else None,
        "district_abbrev": district.abbreviation if district else None,
        "matches": matches,
        "match_count": match_count,
        "matches_recent": matches_recent,
        "matches_upcoming": matches_upcoming,
        "has_time_predictions": has_time_predictions,
        "awards": awards,
        "teams_a": teams_a,
        "teams_b": teams_b,
        "num_teams": num_teams,
        "matchstat_choices": list(matchstats.keys()),
        "matchstat_json": json.dumps(matchstats),
        "matchstat_dropdown_id_map": matchstat_dropdown_id_map,
        "bracket_table": bracket_table,
        "playoff_advancement": playoff_advancement,
        "playoff_template": playoff_template,
        "playoff_advancement_tiebreakers": None,  # PlayoffAdvancementHelper.ROUND_ROBIN_TIEBREAKERS.get(event.year),
        "district_points_sorted": district_points_sorted,
        "event_insights_qual": event_insights["qual"] if event_insights else None,
        "event_insights_playoff": event_insights["playoff"] if event_insights else None,
        "event_insights_template": event_insights_template,
        "medias_by_slugname": medias_by_slugname,
        "event_divisions": event_divisions,
        "parent_event": parent_event_future.get_result()
        if parent_event_future
        else None,
        "double_elim_matches": double_elim_matches,
        "double_elim_playoff_types": playoff_type.DOUBLE_ELIM_TYPES,
    }

    return render_template("event_details.html", template_values)
