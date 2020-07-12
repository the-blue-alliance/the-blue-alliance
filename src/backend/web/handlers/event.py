import logging
from typing import Optional

from flask import abort, redirect, request
from werkzeug.wrappers import Response

from backend.common.decorators import cached_public
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event
from backend.common.models.keys import Year
from backend.common.queries import district_query, event_query
from backend.web.profiled_render import render_template


@cached_public
def event_list(year: Optional[Year] = None) -> Response:
    logging.info(f"REQ YEAR {year}")
    explicit_year = year is not None
    if year is None:
        year = SeasonHelper.get_current_season()

    valid_years = SeasonHelper.get_valid_years()
    if year not in valid_years:
        abort(400)

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
