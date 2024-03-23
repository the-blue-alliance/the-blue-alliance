import json
import logging
from typing import List, Optional

from flask import abort, Blueprint, make_response, render_template, request, url_for
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from werkzeug.wrappers import Response

from backend.common.consts.event_type import EventType, SEASON_EVENT_TYPES
from backend.common.futures import TypedFuture
from backend.common.helpers.district_helper import DistrictHelper
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.event_insights_helper import EventInsightsHelper
from backend.common.helpers.event_team_updater import EventTeamUpdater
from backend.common.helpers.listify import listify
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.matchstats_helper import MatchstatsHelper
from backend.common.helpers.prediction_helper import PredictionHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.manipulators.district_manipulator import DistrictManipulator
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.models.district import District
from backend.common.models.district_ranking import DistrictRanking
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.keys import DistrictKey, EventKey, Year
from backend.common.models.team import Team
from backend.common.queries.district_query import DistrictsInYearQuery
from backend.common.queries.event_query import DistrictEventsQuery, EventListQuery
from backend.common.queries.team_query import DistrictTeamsQuery


blueprint = Blueprint("math", __name__)


@blueprint.route("/tasks/math/enqueue/district_points_calc/<int:year>")
@blueprint.route("/tasks/math/enqueue/district_points_calc", defaults={"year": None})
def enqueue_event_district_points_calc(year: Optional[Year]) -> Response:
    """
    Enqueues calculation of district points for all season events for a given year
    """
    if year is None:
        year = SeasonHelper.get_current_season()

    event_keys: List[ndb.Key] = Event.query(
        Event.year == year, Event.event_type_enum.IN(SEASON_EVENT_TYPES)
    ).fetch(None, keys_only=True)
    for event_key in event_keys:
        taskqueue.add(
            url=url_for(
                "math.event_district_points_calc", event_key=event_key.string_id()
            ),
            method="GET",
            target="py3-tasks-io",
            queue_name="default",
        )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            "Enqueued for: {}".format([event_key.id() for event_key in event_keys])
        )

    return make_response("")


@blueprint.route("/tasks/math/do/district_points_calc/<event_key>")
def event_district_points_calc(event_key: EventKey) -> Response:
    """
    Calculates district points for an event
    """
    event = Event.get_by_id(event_key)
    if event is None:
        abort(404)

    if event.event_type_enum not in SEASON_EVENT_TYPES and not request.args.get(
        "allow-offseason", None
    ):
        return make_response(
            f"Can't calculate district points for a non-season event {event.key_name}!",
            400,
        )

    district_points = DistrictHelper.calculate_event_points(event)
    event_details = EventDetails(id=event_key, district_points=district_points)
    EventDetailsManipulator.createOrUpdate(event_details)

    # Enqueue task to update rankings
    if event.district_key:
        taskqueue.add(
            url=url_for(
                "math.district_rankings_calc",
                district_key=event.district_key.string_id(),
            ),
            method="GET",
            target="py3-tasks-io",
            queue_name="default",
        )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(json.dumps(district_points, sort_keys=True, indent=2))

    return make_response("")


@blueprint.route("/tasks/math/enqueue/district_rankings_calc/<int:year>")
@blueprint.route("/tasks/math/enqueue/district_rankings_calc", defaults={"year": None})
def enqueue_district_rankings_calc(year: Optional[Year]) -> Response:
    """
    Enqueues calculation of rankings for all districts for a given year
    """

    if year is None:
        year = SeasonHelper.get_current_season()

    districts = DistrictsInYearQuery(int(year)).fetch()
    district_keys = [district.key.id() for district in districts]
    for district_key in district_keys:
        taskqueue.add(
            url=url_for("math.district_rankings_calc", district_key=district_key),
            method="GET",
            target="py3-tasks-io",
            queue_name="default",
        )
        taskqueue.add(
            url=url_for("frc_api.district_rankings", district_key=district_key),
            method="GET",
            target="py3-tasks-io",
            queue_name="default",
        )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(f"Enqueued for: {district_keys}")
    return make_response("")


@blueprint.route("/tasks/math/do/district_rankings_calc/<district_key>")
def district_rankings_calc(district_key: DistrictKey) -> Response:
    """
    Calculates district rankings for a district year
    """
    district = District.get_by_id(district_key)
    if not district:
        return make_response(f"District {district_key} not found", 404)

    events_future: TypedFuture[List[Event]] = DistrictEventsQuery(
        district_key
    ).fetch_async()
    teams_future: TypedFuture[List[Team]] = DistrictTeamsQuery(
        district_key
    ).fetch_async()

    events = events_future.get_result()
    for event in events:
        event.prep_details()
    events = EventHelper.sorted_events(events)
    team_totals = DistrictHelper.calculate_rankings(events, teams_future, district.year)

    rankings: List[DistrictRanking] = []
    current_rank = 1
    for key, points in team_totals.items():
        point_detail = DistrictRanking(
            rank=current_rank,
            team_key=key,
            event_points=[],
            rookie_bonus=points.get("rookie_bonus", 0),
            point_total=points["point_total"],
        )
        for event, event_points in points["event_points"]:
            event_points["event_key"] = event.key_name
            event_points["district_cmp"] = (
                event.event_type_enum == EventType.DISTRICT_CMP
                or event.event_type_enum == EventType.DISTRICT_CMP_DIVISION
            )
            point_detail["event_points"].append(event_points)

        if district.year == 2022:
            point_detail["other_bonus"] = points.get("other_bonus", 0)

        rankings.append(point_detail)
        current_rank += 1

    if rankings:
        district.rankings = rankings
        DistrictManipulator.createOrUpdate(district)

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            f"Finished calculating rankings for: {district_key}:\n{rankings}"
        )
    return make_response("")


@blueprint.route("/tasks/math/enqueue/event_matchstats/now", defaults={"year": None})
@blueprint.route("/tasks/math/enqueue/event_matchstats/<int:year>")
def enqueue_event_matchstats(year: Optional[Year]) -> str:
    """
    Enqueues Matchstats calculation
    """
    if year is None:
        events = EventHelper.events_within_a_day()
    else:
        events: List[Event] = EventListQuery(year=year).fetch()

    events = EventHelper.sorted_events(events)
    for event in events:
        taskqueue.add(
            url="/tasks/math/do/event_matchstats/" + event.key_name,
            method="GET",
            target="py3-tasks-io",
            queue_name="run-in-order",  # Because predictions depend on past events
        )

    template_values = {
        "event_count": len(events),
        "year": year,
    }

    return render_template("math/event_matchstats_enqueue.html", **template_values)


@blueprint.route("/tasks/math/do/event_matchstats/<event_key>")
def event_matchstats_calc(event_key: EventKey) -> Response:
    """
    Calculates match stats (OPR/DPR/CCWM) for an event
    Calculates predictions for an event
    Calculates insights for an event
    """
    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    matchstats_dict = MatchstatsHelper.calculate_matchstats(event.matches, event.year)
    print(matchstats_dict)
    if not any([v != {} for v in matchstats_dict.values()]):
        logging.warning("Matchstat calculation for {} failed!".format(event_key))
        matchstats_dict = None

    coprs_dict = MatchstatsHelper.calculate_coprs(event.matches, event.year)
    if len(coprs_dict.keys()) == 0:
        logging.warning(f"COPR calculation for {event_key} failed!")
        coprs_dict = None

    predictions_dict = None
    if (
        event.year in {2016, 2017, 2018, 2019, 2020, 2022, 2023, 2024}
        and event.event_type_enum in SEASON_EVENT_TYPES
    ) or event.enable_predictions:
        sorted_matches = MatchHelper.play_order_sorted_matches(event.matches)
        (
            match_predictions,
            match_prediction_stats,
            stat_mean_vars,
        ) = PredictionHelper.get_match_predictions(sorted_matches)
        (
            ranking_predictions,
            ranking_prediction_stats,
        ) = PredictionHelper.get_ranking_predictions(sorted_matches, match_predictions)

        predictions_dict = {
            "match_predictions": match_predictions,
            "match_prediction_stats": match_prediction_stats,
            "stat_mean_vars": stat_mean_vars,
            "ranking_predictions": ranking_predictions,
            "ranking_prediction_stats": ranking_prediction_stats,
        }

    event_insights = EventInsightsHelper.calculate_event_insights(
        event.matches, event.year
    )

    event_details = EventDetails(
        id=event_key,
        matchstats=matchstats_dict,
        predictions=predictions_dict,
        insights=event_insights,
        coprs=coprs_dict,
    )
    EventDetailsManipulator.createOrUpdate(event_details)

    template_values = {
        "matchstats_dict": matchstats_dict,
        "coprs_dict": coprs_dict,
        "event_insights": event_insights,
    }

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("math/event_matchstats_do.html", **template_values)
        )

    return make_response("")


@blueprint.route("/tasks/math/enqueue/eventteam_update/<when>")
def enqueue_eventteam_update(when: str) -> Response:
    event_keys: List[ndb.Key] = []
    if when == "current":
        event_keys = Event.query(Event.year == SeasonHelper.get_current_season()).fetch(
            1000, keys_only=True
        )
    elif not when.isdigit() or int(when) not in SeasonHelper.get_valid_years():
        abort(404)
    else:
        event_keys = Event.query(Event.year == int(when)).fetch(1000, keys_only=True)

    for event_key in event_keys:
        taskqueue.add(
            url=url_for("math.update_eventteams", event_key=event_key.string_id()),
            method="GET",
        )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        template_values = {
            "event_keys": event_keys,
        }
        return make_response(
            render_template("math/eventteam_update_enqueue.html", **template_values)
        )

    return make_response("")


@blueprint.route("/tasks/math/do/eventteam_update/<event_key>")
def update_eventteams(event_key: EventKey) -> Response:
    """
    Task that updates the EventTeam index for an Event.
    Can only update or delete EventTeams for unregistered teams.
    ^^^ Does it actually do this? Eugene -- 2013/07/30
    """
    if not Event.validate_key_name(event_key):
        abort(404)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    allow_deletes = request.args.get(
        "allow_deletes", False, type=lambda v: v.lower() == "true"
    )
    _, event_teams, et_keys_to_del = EventTeamUpdater.update(event_key, allow_deletes)

    if event_teams:
        event_teams = list(filter(lambda et: et.team.get() is not None, event_teams))
        event_teams = listify(EventTeamManipulator.createOrUpdate(event_teams))

    if et_keys_to_del:
        EventTeamManipulator.delete_keys(et_keys_to_del)

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        template_values = {
            "event_teams": event_teams,
            "deleted_event_teams_keys": et_keys_to_del,
        }

        return make_response(
            render_template("math/eventteam_update_do.html", **template_values)
        )

    return make_response("")
