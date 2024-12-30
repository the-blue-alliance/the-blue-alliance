import datetime
import logging
import re
from typing import List, Optional, Set

from flask import Blueprint, make_response, render_template, request, Response, url_for
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from markupsafe import Markup
from pyre_extensions import none_throws

from backend.common.environment import Environment
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.event_remapteams_helper import EventRemapTeamsHelper
from backend.common.helpers.listify import listify
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.offseason_event_helper import OffseasonEventHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.manipulators.award_manipulator import AwardManipulator
from backend.common.manipulators.district_manipulator import DistrictManipulator
from backend.common.manipulators.district_team_manipulator import (
    DistrictTeamManipulator,
)
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.manipulators.robot_manipulator import RobotManipulator
from backend.common.manipulators.team_manipulator import TeamManipulator
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import DistrictKey, EventKey, TeamKey, Year
from backend.common.models.robot import Robot
from backend.common.models.team import Team
from backend.common.sitevars.apistatus import ApiStatus
from backend.common.sitevars.cmp_registration_hacks import ChampsRegistrationHacks
from backend.common.suggestions.suggestion_creator import SuggestionCreator
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI

blueprint = Blueprint("frc_api", __name__)


@blueprint.route("/tasks/enqueue/fmsapi_team_details_rolling")
def enqueue_rolling_team_details() -> Response:
    """
    Handles enqueing updates to individual teams
    Enqueues a certain fraction of teams so that all teams will get updated
    every PERIOD days.
    """
    PERIOD = 14  # a particular team will be updated every PERIOD days
    days_since_epoch = (datetime.datetime.now() - datetime.datetime(1970, 1, 1)).days
    bucket_num = int(days_since_epoch % PERIOD)

    highest_team_key = Team.query().order(-Team.team_number).fetch(1, keys_only=True)[0]
    highest_team_num = int(highest_team_key.id()[3:])
    bucket_size = int(highest_team_num // PERIOD) + 1

    min_team = bucket_num * bucket_size
    max_team = min_team + bucket_size
    team_keys = Team.query(
        Team.team_number >= min_team, Team.team_number < max_team
    ).fetch(1000, keys_only=True)

    teams = ndb.get_multi(team_keys)
    for team in teams:
        taskqueue.add(
            queue_name="datafeed",
            target="py3-tasks-io",
            url=url_for("frc_api.team_details", team_key=team.key_name),
            method="GET",
        )

    template_values = {
        "bucket_num": bucket_num,
        "period": PERIOD,
        "team_count": len(teams),
        "min_team": min_team,
        "max_team": max_team,
    }

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template(
                "datafeeds/rolling_team_details_enqueue.html", **template_values
            )
        )

    return make_response("")


@blueprint.route("/backend-tasks/get/team_details/<team_key>")
def team_details(team_key: TeamKey) -> Response:
    if not Team.validate_key_name(team_key):
        return make_response(f"Bad team key: {Markup.escape(team_key)}", 400)

    fms_df = DatafeedFMSAPI(save_response=True)
    year = datetime.date.today().year
    fms_details = fms_df.get_team_details(year, team_key)

    team, district_team, robot = fms_details or (None, None, None)

    if team:
        team = TeamManipulator.createOrUpdate(team, update_manual_attrs=False)

    if district_team:
        district_team = DistrictTeamManipulator.createOrUpdate(
            district_team, update_manual_attrs=False
        )

    # Clean up junk district teams
    # https://www.facebook.com/groups/moardata/permalink/1310068625680096/
    if team:
        keys_to_delete = set()
        # Delete all DistrictTeams that are not valid in the current
        # year, since each team can only be in one district per year
        dt_keys = DistrictTeam.query(
            DistrictTeam.team == team.key, DistrictTeam.year == year
        ).fetch(keys_only=True)
        for dt_key in dt_keys:
            if not district_team or dt_key.id() != district_team.key.id():
                keys_to_delete.add(dt_key)

        # Delete all DistrictTeam that are for any year that the team
        # does not have an event
        dt_keys = DistrictTeam.query(DistrictTeam.team == team.key).fetch()
        et_keys = EventTeam.query(
            EventTeam.team == team.key,
            projection=[EventTeam.year],
            group_by=[EventTeam.year],
        ).fetch()
        et_years = {et_key.year for et_key in et_keys}

        for dt_key in dt_keys:
            if dt_key.year not in et_years:
                keys_to_delete.add(dt_key.key)
        DistrictTeamManipulator.delete_keys(keys_to_delete)

    if robot:
        robot = RobotManipulator.createOrUpdate(robot, update_manual_attrs=False)

    template_values = {
        "key_name": team_key,
        "team": team,
        "success": team is not None,
        "robot": robot,
        "district_team": district_team,
    }

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template(
                "datafeeds/usfirst_team_details_get.html", **template_values
            )
        )

    return make_response("")


@blueprint.route("/backend-tasks/get/team_avatar/<team_key>")
def team_avatar(team_key: TeamKey) -> Response:
    if not Team.validate_key_name(team_key):
        return make_response(f"Bad team key: {Markup.escape(team_key)}", 400)
    team = Team.get_by_id(team_key)

    fms_df = DatafeedFMSAPI(save_response=True)
    year = datetime.date.today().year

    avatar, keys_to_delete = fms_df.get_team_avatar(year, team_key)

    if avatar:
        MediaManipulator.createOrUpdate(avatar, update_manual_attrs=False)

    MediaManipulator.delete_keys(keys_to_delete)

    template_values = {
        "key_name": team_key,
        "team": team,
        "success": avatar is not None,
    }

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("datafeeds/usfirst_team_avatar_get.html", **template_values)
        )

    return make_response("")


@blueprint.route("/backend-tasks/enqueue/event_list/current", defaults={"year": None})
@blueprint.route("/backend-tasks/enqueue/event_list/<int:year>")
def enqueue_event_list(year: Optional[Year]) -> Response:
    years: List[Year]

    if year is None:
        api_status_sv = ApiStatus.get()
        current_year = api_status_sv["current_season"]
        max_year = api_status_sv["max_season"]
        years = list(range(current_year, max_year + 1))
    else:
        years = [year]

    for year_to_fetch in years:
        taskqueue.add(
            queue_name="datafeed",
            target="py3-tasks-io",
            url=url_for("frc_api.event_list", year=year_to_fetch),
            method="GET",
        )

    template_values = {"years": years}

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template(
                "datafeeds/usfirst_events_details_enqueue.html", **template_values
            )
        )

    return make_response("")


@blueprint.route("/backend-tasks/get/event_list/<int:year>")
def event_list(year: Year) -> Response:
    df = DatafeedFMSAPI(save_response=True)

    fmsapi_events, event_list_districts = df.get_event_list(year)

    # All regular-season events can be inserted without any work involved.
    # We need to de-duplicate offseason events from the FRC Events API with a different code than the TBA event code
    fmsapi_events_offseason = [e for e in fmsapi_events if e.is_offseason]
    event_keys_to_put = set([e.key_name for e in fmsapi_events]) - set(
        [e.key_name for e in fmsapi_events_offseason]
    )
    events_to_put = [e for e in fmsapi_events if e.key_name in event_keys_to_put]

    (
        matched_offseason_events,
        new_offseason_events,
    ) = OffseasonEventHelper.categorize_offseasons(int(year), fmsapi_events_offseason)

    # For all matched offseason events, make sure the FIRST code matches the TBA FIRST code
    for tba_event, first_event in matched_offseason_events:
        tba_event.first_code = first_event.event_short
        events_to_put.append(tba_event)  # Update TBA events - discard the FIRST event

    # For all new offseason events we can't automatically match, create suggestions
    SuggestionCreator.createDummyOffseasonSuggestions(new_offseason_events)

    events = (
        listify(
            EventManipulator.createOrUpdate(events_to_put, update_manual_attrs=False)
        )
        or []
    )

    fmsapi_districts = df.get_district_list(year)
    merged_districts = DistrictManipulator.mergeModels(
        fmsapi_districts, event_list_districts
    )
    districts = listify(
        DistrictManipulator.createOrUpdate(merged_districts, update_manual_attrs=False)
    )

    # Fetch event details for each event
    for event in events:
        taskqueue.add(
            queue_name="datafeed",
            target="py3-tasks-io",
            url=url_for("frc_api.event_details", event_key=event.key_name),
            method="GET",
        )

    template_values = {
        "events": events,
        "districts": districts,
    }

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("datafeeds/fms_event_list_get.html", **template_values)
        )

    return make_response("")


@blueprint.route("/backend-tasks/enqueue/event_details/<event_key>")
def enqueue_event_details(event_key: EventKey) -> Response:
    if not Event.validate_key_name(event_key):
        return make_response(f"Bad event key: {Markup.escape(event_key)}", 400)

    taskqueue.add(
        queue_name="datafeed",
        target="py3-tasks-io",
        url=url_for("frc_api.event_details", event_key=event_key),
        method="GET",
    )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            make_response(
                render_template(
                    "datafeeds/fmsapi_eventteams_enqueue.html", event_key=event_key
                )
            )
        )

    return make_response("")


@blueprint.route("/backend-tasks/get/event_details/<event_key>")
def event_details(event_key: EventKey) -> Response:
    if not Event.validate_key_name(event_key):
        return make_response(f"Bad event key: {Markup.escape(event_key)}", 400)

    df = DatafeedFMSAPI(save_response=True)

    # Update event
    fmsapi_events, fmsapi_districts = df.get_event_details(event_key)
    event = EventManipulator.createOrUpdate(fmsapi_events[0], update_manual_attrs=False)

    DistrictManipulator.createOrUpdate(fmsapi_districts, update_manual_attrs=False)

    models = df.get_event_teams(event_key)
    teams: List[Team] = []
    district_teams: List[DistrictTeam] = []
    robots: List[Robot] = []
    for group in models:
        # models is a list of tuples (team, districtTeam, robot)
        team = group[0]
        if isinstance(team, Team):
            teams.append(team)

        district_team = group[1]
        if isinstance(district_team, DistrictTeam):
            district_teams.append(district_team)

        robot = group[2]
        if isinstance(robot, Robot):
            robots.append(robot)

    # Write new models
    if (
        teams and event.year == SeasonHelper.get_max_year() or Environment.is_dev()
    ):  # Only update from latest year
        teams = TeamManipulator.createOrUpdate(teams, update_manual_attrs=False)

    district_teams = DistrictTeamManipulator.createOrUpdate(
        district_teams, update_manual_attrs=False
    )
    robots = RobotManipulator.createOrUpdate(robots, update_manual_attrs=False)

    if not teams:
        # No teams found registered for this event
        teams = []
    if type(teams) is not list:
        teams = [teams]

    # Build EventTeams
    skip_eventteams = ChampsRegistrationHacks.should_skip_eventteams(event)
    event_teams = (
        [
            EventTeam(
                id=event.key_name + "_" + team.key_name,
                event=event.key,
                team=team.key,
                year=event.year,
            )
            for team in teams
        ]
        if not skip_eventteams
        else []
    )

    # Delete eventteams of teams that are no longer registered
    if event_teams and not skip_eventteams:
        existing_event_teams = EventTeam.query(EventTeam.event == event.key).fetch()

        # Don't delete EventTeam models for teams who won Awards at the Event, but who did not attend the Event
        award_teams = set()
        for award in event.awards:
            for team in award.team_list:
                award_teams.add(team.id())
        award_event_teams = {
            et.key for et in existing_event_teams if et.team.id() in award_teams
        }

        event_team_keys = {et.key for et in event_teams}
        existing_event_team_keys = {et.key for et in existing_event_teams}

        et_keys_to_delete = existing_event_team_keys.difference(
            event_team_keys.union(award_event_teams)
        )
        EventTeamManipulator.delete_keys(et_keys_to_delete)

    if skip_eventteams:
        # If we're skipping team registrations from upstream,
        # enqueue a recalculation using local data
        logging.info(
            f"SKipping eventteams, enqueueing local computation for {event_key}"
        )
        taskqueue.add(
            url=url_for("math.update_eventteams", event_key=event_key),
            method="GET",
            target="py3-tasks-io",
            params={"allow_deletes": True},
        )

    event_teams = EventTeamManipulator.createOrUpdate(
        event_teams, update_manual_attrs=False
    )
    if type(event_teams) is not list:
        event_teams = [event_teams]

    if event.year >= 2018:
        avatars, keys_to_delete = df.get_event_team_avatars(event.key_name)
        if avatars:
            MediaManipulator.createOrUpdate(avatars, update_manual_attrs=False)
        MediaManipulator.delete_keys(keys_to_delete)

    template_values = {
        "event": event,
        "event_teams": event_teams,
    }

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template(
                "datafeeds/usfirst_event_details_get.html", **template_values
            )
        )

    return make_response("")


@blueprint.route(
    "/tasks/enqueue/fmsapi_event_alliances/last_day_only",
    defaults={"year": None, "when": "last_day_only"},
)
@blueprint.route(
    "/tasks/enqueue/fmsapi_event_alliances/now", defaults={"year": None, "when": "now"}
)
@blueprint.route("/tasks/enqueue/fmsapi_event_alliances/<int:year>")
def enqueue_event_alliances(
    year: Optional[Year], when: Optional[str] = None
) -> Response:
    events: List[Event]
    if when == "now":
        events = EventHelper.events_within_a_day()
        events = list(filter(lambda e: e.official, events))
    elif when == "last_day_only":
        events = EventHelper.events_within_a_day()
        events = list(filter(lambda e: e.official and e.ends_today, events))
    else:
        event_keys = (
            Event.query(Event.official == True)  # noqa: E712
            .filter(Event.year == year)
            .fetch(500, keys_only=True)
        )
        events = ndb.get_multi(event_keys)

    for event in events:
        taskqueue.add(
            queue_name="datafeed",
            target="py3-tasks-io",
            url=url_for("frc_api.event_alliances", event_key=event.key_name),
            method="GET",
        )

    template_values = {"events": events}

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template(
                "datafeeds/usfirst_event_alliances_enqueue.html", **template_values
            )
        )

    return make_response("")


@blueprint.route("/tasks/get/fmsapi_event_alliances/<event_key>")
def event_alliances(event_key: EventKey) -> Response:
    df = DatafeedFMSAPI(save_response=True)
    event = Event.get_by_id(event_key) if Event.validate_key_name(event_key) else None
    if not event:
        return make_response(f"No Event for key: {Markup.escape(event_key)}", 404)

    alliance_selections = df.get_event_alliances(event_key)

    if event and event.remap_teams:
        EventRemapTeamsHelper.remapteams_alliances(
            alliance_selections, event.remap_teams
        )

    event_details = EventDetails(id=event_key, alliance_selections=alliance_selections)
    EventDetailsManipulator.createOrUpdate(event_details, update_manual_attrs=False)

    template_values = {
        "alliance_selections": alliance_selections,
        "event_name": event_details.key.id(),
    }

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template(
                "datafeeds/usfirst_event_alliances_get.html", **template_values
            )
        )
    return make_response("")


@blueprint.route("/tasks/enqueue/fmsapi_event_rankings/now", defaults={"year": None})
@blueprint.route("/tasks/enqueue/fmsapi_event_rankings/<int:year>")
def enqueue_event_rankings(year: Optional[Year]) -> Response:
    events: List[Event] = []
    if year is None:
        events = EventHelper.events_within_a_day()
        events = list(filter(lambda e: e.official, events))
    else:
        event_keys = (
            Event.query(Event.official == True)  # noqa: 712
            .filter(Event.year == year)
            .fetch(500, keys_only=True)
        )
        events = ndb.get_multi(event_keys)

    for event in events:
        taskqueue.add(
            queue_name="datafeed",
            target="py3-tasks-io",
            url=url_for("frc_api.event_rankings", event_key=event.key_name),
            method="GET",
        )

    template_values = {
        "events": events,
    }

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template(
                "datafeeds/usfirst_event_rankings_enqueue.html", **template_values
            )
        )

    return make_response("")


@blueprint.route("/tasks/get/fmsapi_event_rankings/<event_key>")
def event_rankings(event_key: EventKey) -> Response:
    df = DatafeedFMSAPI(save_response=True)
    event = Event.get_by_id(event_key) if Event.validate_key_name(event_key) else None
    if event is None:
        return make_response(f"No Event for key: {Markup.escape(event_key)}", 404)

    rankings2 = df.get_event_rankings(event_key)

    if event and event.remap_teams:
        EventRemapTeamsHelper.remapteams_rankings2(rankings2, event.remap_teams)

    event_details = EventDetails(id=event_key, rankings2=rankings2)
    EventDetailsManipulator.createOrUpdate(event_details, update_manual_attrs=False)

    template_values = {"rankings": rankings2, "event_name": event_details.key.id()}

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template(
                "datafeeds/usfirst_event_rankings_get.html", **template_values
            )
        )

    return make_response("")


@blueprint.route("/tasks/enqueue/fmsapi_matches/now", defaults={"year": None})
@blueprint.route("/tasks/enqueue/fmsapi_matches/<int:year>")
def enqueue_event_matches(year: Optional[Year]) -> Response:
    events: List[Event]
    if year is None:
        events = EventHelper.events_within_a_day()
        events = list(filter(lambda e: e.official, events))
    else:
        event_keys = (
            Event.query(Event.official == True)  # noqa: E712
            .filter(Event.year == year)
            .fetch(500, keys_only=True)
        )
        events = ndb.get_multi(event_keys)

    for event in events:
        taskqueue.add(
            queue_name="datafeed",
            target="py3-tasks-io",
            url=url_for("frc_api.event_matches", event_key=event.key_name),
            method="GET",
        )

    template_values = {
        "events": events,
    }

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("datafeeds/usfirst_matches_enqueue.html", **template_values)
        )

    return make_response("")


@blueprint.route("/tasks/get/fmsapi_matches/<event_key>")
def event_matches(event_key: EventKey) -> Response:
    event = Event.get_by_id(event_key) if Event.validate_key_name(event_key) else None
    if event is None:
        return make_response(f"No Event for key: {Markup.escape(event_key)}", 404)

    # Prefetch exisitng matches to merge with new matches
    event.prep_matches()

    df = DatafeedFMSAPI(save_response=True)
    matches = df.get_event_matches(event_key)
    existing_matches = event.matches

    # Add existing matches to the new matches if they aren't present.
    # This is necessary so we can delete matches that are no longer valid.
    new_match_keys = set([m.key.id() for m in matches])
    for match in existing_matches:
        if match.key.id() not in new_match_keys:
            matches.append(match)

    matches, keys_to_delete = MatchHelper.delete_invalid_matches(
        matches,
        event,
    )
    matches = listify(matches)

    if event and event.remap_teams:
        EventRemapTeamsHelper.remapteams_matches(matches, event.remap_teams)

    MatchManipulator.delete_keys(keys_to_delete)
    new_matches = listify(
        MatchManipulator.createOrUpdate(matches, update_manual_attrs=False)
    )

    template_values = {"matches": new_matches, "deleted_keys": keys_to_delete}

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("datafeeds/usfirst_matches_get.html", **template_values)
        )

    return make_response("")


# @blueprint.route("/awards")
# @blueprint.route("/awards/<int:from backend.common.helpers.listify import delistify, listifyyear>")
# TODO: Drop support for this "now" and just use an empty year
@blueprint.route("/tasks/enqueue/fmsapi_awards/now", defaults={"year": None})
@blueprint.route("/tasks/enqueue/fmsapi_awards/<int:year>")
def awards_year(year: Optional[int]) -> Response:
    events: List[Event]
    if year is None:
        events = EventHelper.events_within_a_day()
        events = list(filter(lambda e: e.official, events))
    else:
        event_keys = (
            Event.query(Event.official == True)  # noqa: E712
            .filter(Event.year == year)
            .fetch(keys_only=True)
        )
        events = ndb.get_multi(event_keys)

    for event in events:
        taskqueue.add(
            queue_name="datafeed",
            target="py3-tasks-io",
            url=url_for("frc_api.awards_event", event_key=event.key_name),
            method="GET",
        )

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("datafeeds/fmsapi_awards_enqueue.html", events=events)
        )

    return make_response("")


# @blueprint.route("/awards/<event_key>")
@blueprint.route("/tasks/get/fmsapi_awards/<event_key>")
def awards_event(event_key: EventKey) -> Response:
    event = Event.get_by_id(event_key) if Event.validate_key_name(event_key) else None
    if event is None:
        return make_response(f"No Event for key: {Markup.escape(event_key)}", 404)

    datafeed = DatafeedFMSAPI(save_response=True)
    awards = datafeed.get_awards(event)

    if event.remap_teams:
        EventRemapTeamsHelper.remapteams_awards(awards, event.remap_teams)

    new_awards = AwardManipulator.createOrUpdate(awards, update_manual_attrs=False)
    # new_awards could be a single object or None
    new_awards = listify(new_awards)

    # Create EventTeams
    team_ids: Set[TeamKey] = set()
    for award in new_awards:
        for team in award.team_list:
            team_id = none_throws(team.string_id())
            # strip all suffixes (eg B teams)
            team_ids.add("frc" + re.sub("[^0-9]", "", team_id))

    teams = TeamManipulator.createOrUpdate(
        [Team(id=team_id, team_number=int(team_id[3:])) for team_id in team_ids],
        update_manual_attrs=False,
    )

    if teams:
        # teams might be a single object
        teams = listify(teams)

        EventTeamManipulator.createOrUpdate(
            [
                EventTeam(
                    id=event_key + "_" + team.key_name,
                    event=event.key,
                    team=team.key,
                    year=event.year,
                )
                for team in teams
            ],
            update_manual_attrs=False,
        )

    # Only write out if not in taskqueue
    if "X-Appengine-Taskname" not in request.headers:
        return make_response(
            render_template("datafeeds/fmsapi_awards_get.html", awards=new_awards)
        )

    return make_response("")


@blueprint.route("/backend-tasks/get/district_list/<int:year>")
def district_list(year: Year) -> Response:
    df = DatafeedFMSAPI()
    fmsapi_districts = df.get_district_list(year)
    districts = DistrictManipulator.createOrUpdate(
        fmsapi_districts, update_manual_attrs=False
    )

    template_values = {
        "districts": listify(districts),
    }

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("datafeeds/fms_district_list_get.html", **template_values)
        )

    return make_response("")


@blueprint.route("/backend-tasks/get/district_rankings/<district_key>")
def district_rankings(district_key: DistrictKey) -> Response:
    district = (
        District.get_by_id(district_key)
        if District.validate_key_name(district_key)
        else None
    )
    if district is None:
        return make_response(f"No District for key: {Markup.escape(district_key)}", 404)

    df = DatafeedFMSAPI()
    advancement = df.get_district_rankings(district_key)
    if advancement:
        district.advancement = advancement
        district = DistrictManipulator.createOrUpdate(
            district, update_manual_attrs=False
        )

    template_values = {
        "districts": listify(district),
    }

    if (
        "X-Appengine-Taskname" not in request.headers
    ):  # Only write out if not in taskqueue
        return make_response(
            render_template("datafeeds/fms_district_list_get.html", **template_values)
        )

    return make_response("")
