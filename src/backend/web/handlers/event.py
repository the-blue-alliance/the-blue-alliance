import collections
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from flask import abort, redirect, request
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.wrappers import Response

from backend.common.consts import comp_level, playoff_type
from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import COMP_LEVELS, CompLevel
from backend.common.consts.event_type import EventType
from backend.common.decorators import cached_public
from backend.common.flask_cache import make_cached_response
from backend.common.helpers.award_helper import AwardHelper
from backend.common.helpers.district_point_tiebreakers_sorting_helper import (
    DistrictPointTiebreakersSortingHelper,
)
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.media_helper import MediaHelper
from backend.common.helpers.playlist_helper import PlaylistHelper
from backend.common.helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.helpers.team_helper import TeamHelper
from backend.common.models.event import Event
from backend.common.models.event_matchstats import Component, TeamStatMap
from backend.common.models.keys import EventKey, TeamId, TeamKey, Year
from backend.common.models.match import Match
from backend.common.queries import district_query, event_query, media_query, team_query
from backend.web.profiled_render import render_template


def convert_component_name(component_name: str) -> str:
    """
    Converts a camelCase componentName to a human readable title case name.

    e.g. foulCount -> Foul Count, totalPoints -> Total Points, OPR -> OPR, rp -> RP
    """
    # for things like OPR that should stay all uppercase
    if component_name.isupper():
        return component_name

    # for things like "rp" that should be totally uppercased
    if component_name in ["rp"]:
        return component_name.upper()

    with_spaces = re.sub("([A-Z])", r" \1", component_name)
    return with_spaces.title()


def sort_and_limit_stats(
    stats_dict: TeamStatMap, num_matchstats: Optional[int] = None
) -> List[Tuple[TeamKey, float]]:
    return sorted(stats_dict.items(), key=lambda t: -t[1])[:num_matchstats]


@cached_public
def event_list(year: Optional[Year] = None) -> Response:
    explicit_year = year is not None
    if year is None:
        year = SeasonHelper.get_current_season()

    valid_years = list(reversed(SeasonHelper.get_valid_years()))
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

    events = EventHelper.sorted_events(events_future.get_result())
    if state_prov == "" or (state_prov and not events):
        return redirect(request.path)

    week_events = EventHelper.group_by_week(events)

    districts = []  # a tuple of (district abbrev, district name)
    for district in districts_future.get_result():
        districts.append((district.abbreviation, district.display_name))
    districts = sorted(districts, key=lambda d: d[1])

    # Special case to display a list of regionals
    if any(map(lambda e: e.event_type_enum == EventType.REGIONAL, events)):
        districts.insert(0, ("regional", "Regional Events"))

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
    return make_cached_response(
        render_template("event_list.html", template_values),
        ttl=timedelta(minutes=5) if year == datetime.now().year else timedelta(days=1),
    )


@cached_public
def event_detail(event_key: EventKey) -> Response:
    event: Optional[Event] = event_query.EventQuery(event_key).fetch()

    if not event:
        abort(404)

    event.prep_awards()
    event.prep_matches()
    event.prep_teams()
    event.prep_details()
    medias_future = media_query.EventTeamsPreferredMediasQuery(event_key).fetch_async()
    district_future = (
        district_query.DistrictQuery(
            none_throws(none_throws(event.district_key).string_id())
        ).fetch_async()
        if event.district_key
        else None
    )
    event_medias_future = media_query.EventMediasQuery(event_key).fetch_async()
    event_eventteams_future = team_query.EventEventTeamsQuery(event_key).fetch_async()
    # status_sitevar_future = Sitevar.get_by_id_async('apistatus.down_events')

    event_divisions_future = None
    event_codivisions_future = None
    parent_event_future = None
    if event.divisions:
        event_divisions_future = ndb.get_multi_async(event.divisions)
    elif event.parent_event:
        parent_event_future = none_throws(event.parent_event).get_async()
        event_codivisions_future = event_query.EventDivisionsQuery(
            none_throws(none_throws(event.parent_event).string_id())
        ).fetch_async()

    awards = AwardHelper.organize_awards(event.awards)
    cleaned_matches = event.matches
    # MatchHelper.delete_invalid_matches(event.matches, event)
    match_count, matches = MatchHelper.organized_matches(cleaned_matches)
    teams = TeamHelper.sort_teams(event.teams)  # pyre-ignore[6]

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

    oprs = []
    copr_leaders: Dict[Component, List[Tuple[TeamId, float]]] = {}

    if event.matchstats is not None:
        oprs = sort_and_limit_stats(event.matchstats.get("oprs") or {})
        copr_leaders["OPR"] = oprs

    if event.coprs is not None:
        for component, tsm in event.coprs.items():
            copr_leaders[component] = sort_and_limit_stats(tsm)

    # Container for (component, componentValidHtmlId, and componentHumanReadableName) elements
    copr_items: List[Tuple[Component, str, str]] = [
        (k, re.sub("[^0-9a-zA-Z]+", "_", k), convert_component_name(k))
        for k in copr_leaders.keys()
    ]

    if event.now:
        matches_recent = MatchHelper.recent_matches(cleaned_matches)
        matches_upcoming = MatchHelper.upcoming_matches(cleaned_matches)
    else:
        matches_recent = None
        matches_upcoming = None

    bracket_table = event.playoff_bracket
    playoff_advancement = event.playoff_advancement
    double_elim_matches = PlayoffAdvancementHelper.double_elim_matches(event, matches)
    playoff_template = PlayoffAdvancementHelper.playoff_template(event)

    district_points_sorted = None
    if event.district_key and (points := event.district_points):
        district_points_sorted = DistrictPointTiebreakersSortingHelper.sorted_points(
            points
        )

    is_regional_cmp_pool_eligible = (
        SeasonHelper.is_valid_regional_pool_year(event.year)
        and event.event_type_enum == EventType.REGIONAL
    )
    regional_champs_pool_points_sorted = None
    if is_regional_cmp_pool_eligible and (points := event.regional_champs_pool_points):
        regional_champs_pool_points_sorted = (
            DistrictPointTiebreakersSortingHelper.sorted_points(points)
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

    qual_playlist = PlaylistHelper.generate_playlist_link(
        matches_organized=matches,
        title=f"{event.year} {event.name} Qualifications",
        allow_levels=[comp_level.CompLevel.QM],
    )
    elim_playlist = PlaylistHelper.generate_playlist_link(
        matches_organized=matches,
        title=f"{event.year} {event.name} Playoffs",
        allow_levels=comp_level.ELIM_LEVELS,
    )

    eventteams = event_eventteams_future.get_result()
    nexus_pit_locations = {
        et.team.string_id(): et.pit_location["location"]
        for et in eventteams
        if et.pit_location
    }

    template_values = {
        "event": event,
        "event_down": False,  # status_sitevar and event_key in status_sitevar.contents,
        "district_name": district.display_name if district else None,
        "district_abbrev": district.abbreviation if district else None,
        "is_regional_cmp_eligible": is_regional_cmp_pool_eligible,
        "matches": matches,
        "match_count": match_count,
        "matches_recent": matches_recent,
        "matches_upcoming": matches_upcoming,
        "has_time_predictions": has_time_predictions,
        "awards": awards,
        "teams_a": teams_a,
        "teams_b": teams_b,
        "num_teams": num_teams,
        "oprs": oprs,
        "bracket_table": bracket_table or {},
        "playoff_advancement": playoff_advancement,
        "playoff_template": playoff_template,
        "playoff_advancement_tiebreakers": PlayoffAdvancementHelper.ROUND_ROBIN_TIEBREAKERS.get(
            event.year, []
        ),
        "district_points_sorted": district_points_sorted,
        "regional_champs_pool_points_sorted": regional_champs_pool_points_sorted,
        "event_insights_qual": event_insights["qual"] if event_insights else None,
        "event_insights_playoff": event_insights["playoff"] if event_insights else None,
        "event_insights_template": event_insights_template,
        "medias_by_slugname": medias_by_slugname,
        "event_divisions": event_divisions,
        "parent_event": (
            parent_event_future.get_result() if parent_event_future else None
        ),
        "double_elim_rounds": playoff_type.DoubleElimRound.__members__.values(),
        "double_elim_matches": double_elim_matches,
        "double_elim_playoff_types": playoff_type.DOUBLE_ELIM_TYPES,
        "qual_playlist": qual_playlist,
        "elim_playlist": elim_playlist,
        "has_coprs": event.coprs is not None,
        "coprs_json": json.dumps(copr_leaders),
        "copr_items": copr_items,
        "nexus_pit_locations": nexus_pit_locations,
    }

    return make_cached_response(
        render_template("event_details.html", template_values),
        ttl=timedelta(seconds=61) if event.within_a_day else timedelta(days=1),
    )


@cached_public
def event_insights(event_key: EventKey) -> Response:
    event: Optional[Event] = event_query.EventQuery(event_key).fetch()

    if not event or event.year < 2016:
        abort(404)

    event.prep_matches()

    event_details = event.details
    event_predictions = event_details.predictions if event_details else None
    if not event_details or not event_predictions:
        abort(404)

    match_predictions = event_predictions.get("match_predictions", None)
    match_prediction_stats = event_predictions.get("match_prediction_stats", None)

    ranking_predictions = event_predictions.get("ranking_predictions", None)
    ranking_prediction_stats = event_predictions.get("ranking_prediction_stats", None)

    # TODO: Unify with API handler
    cleaned_matches, _keys_to_delete = MatchHelper.delete_invalid_matches(
        event.matches, event
    )
    _count, matches = MatchHelper.organized_matches(cleaned_matches)

    # If no matches but there are match predictions, create fake matches
    # For cases where FIRST doesn't allow posting of match schedule
    fake_matches = False
    if match_predictions and (not matches[CompLevel.QM] and match_predictions["qual"]):
        fake_matches = True
        for i in range(len(match_predictions["qual"].keys())):
            match_number = i + 1
            alliances = {
                "red": {"score": -1, "teams": ["frc?", "frc?", "frc?"]},
                "blue": {"score": -1, "teams": ["frc?", "frc?", "frc?"]},
            }
            matches[CompLevel.QM].append(
                Match(
                    id=Match.render_key_name(event_key, CompLevel.QM, 1, match_number),
                    event=event.key,
                    year=event.year,
                    set_number=1,
                    match_number=match_number,
                    comp_level=CompLevel.QM,
                    alliances_json=json.dumps(alliances),
                )
            )

    # Add actual scores to predictions
    distribution_info = {}
    for cmp_level in COMP_LEVELS:
        level = "qual" if cmp_level == CompLevel.QM else "playoff"
        for match in matches[cmp_level]:
            distribution_info[match.key_name] = {
                "level": level,
                "red_actual_score": match.alliances[AllianceColor.RED]["score"],
                "blue_actual_score": match.alliances[AllianceColor.BLUE]["score"],
                "red_mean": (
                    match_predictions[level][match.key_name]["red"]["score"]
                    if match_predictions
                    else 0
                ),
                "blue_mean": (
                    match_predictions[level][match.key_name]["blue"]["score"]
                    if match_predictions
                    else 0
                ),
                "red_var": (
                    match_predictions[level][match.key_name]["red"]["score_var"]
                    if match_predictions
                    else 0
                ),
                "blue_var": (
                    match_predictions[level][match.key_name]["blue"]["score_var"]
                    if match_predictions
                    else 0
                ),
            }

    last_played_match_num = None
    if ranking_prediction_stats:
        last_played_match_key = ranking_prediction_stats.get("last_played_match", None)
        if last_played_match_key:
            last_played_match_num = last_played_match_key.split("_qm")[1]

    template_values = {
        "event": event,
        "matches": matches,
        "fake_matches": fake_matches,
        "match_predictions": match_predictions,
        "distribution_info_json": json.dumps(distribution_info),
        "match_prediction_stats": match_prediction_stats,
        "ranking_predictions": ranking_predictions,
        "ranking_prediction_stats": ranking_prediction_stats,
        "last_played_match_num": last_played_match_num,
    }

    return make_cached_response(
        render_template("event_insights.html", template_values),
        ttl=timedelta(seconds=61) if event.within_a_day else timedelta(days=1),
    )


@cached_public
def event_rss(event_key: EventKey) -> Response:
    event: Optional[Event] = event_query.EventQuery(event_key).fetch()

    if not event:
        return redirect("/events")

    cleaned_matches = event.matches
    _, matches = MatchHelper.organized_matches(cleaned_matches)

    template_values = {
        "event": event,
        "matches": matches,
        "datetime": datetime.now(),
    }

    response = make_cached_response(
        render_template("event_rss.xml", template_values),
        ttl=timedelta(seconds=61) if event.within_a_day else timedelta(days=1),
    )
    response.headers["content-type"] = "application/xml; charset=UTF-8"

    return response


def event_agenda(event_key: EventKey) -> Response:
    if (
        not Event.validate_key_name(event_key)
        or not (event := Event.get_by_id(event_key))
        or not (agenda_url := event.public_agenda_url)
    ):
        abort(404)

    return redirect(agenda_url)
