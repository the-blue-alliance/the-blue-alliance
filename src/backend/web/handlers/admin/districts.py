from datetime import datetime
from typing import Optional

from flask import abort, redirect, request, url_for
from werkzeug import Response

from backend.common.helpers.season_helper import SeasonHelper
from backend.common.manipulators.district_manipulator import DistrictManipulator
from backend.common.manipulators.district_team_manipulator import (
    DistrictTeamManipulator,
)
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.keys import DistrictKey, Year
from backend.web.profiled_render import render_template


def district_list(year: Optional[Year]) -> str:
    if not year:
        year = datetime.now().year

    districts = District.query(District.year == year).fetch(10000)
    template_values = {
        "valid_years": reversed(SeasonHelper.get_valid_district_years()),
        "selected_year": year,
        "districts": districts,
    }

    return render_template("admin/district_list.html", template_values)


def district_details(district_key: DistrictKey) -> str:
    district = District.get_by_id(district_key)
    if not district:
        abort(404)

    events = Event.query(Event.district_key == district.key).fetch_async()
    template_values = {"district": district, "events": events.get_result()}
    return render_template("admin/district_details.html", template_values)


def district_edit(district_key: DistrictKey) -> str:
    district = District.get_by_id(district_key)
    if district is None:
        abort(404)

    template_values = {"district": district}
    return render_template("admin/district_edit.html", template_values)


def district_edit_post(district_key: Optional[DistrictKey]) -> Response:
    year = int(request.form["year"])
    abbreviation = request.form["abbreviation"]
    display_name = request.form.get("display_name")

    if district_key is None:
        district_key = District.render_key_name(year, abbreviation)

    if not District.validate_key_name(district_key):
        abort(400)

    district = District(
        id=district_key,
        year=year,
        abbreviation=abbreviation,
        display_name=display_name,
    )
    DistrictManipulator.createOrUpdate(district)

    return redirect(url_for("admin.district_list", year=district.year))


def district_create() -> str:
    return render_template("admin/district_create.html")


def district_delete(district_key: DistrictKey) -> str:
    district = District.get_by_id(district_key)
    if district is None:
        abort(404)

    template_values = {"district": district}
    return render_template("admin/district_delete.html", template_values)


def district_delete_post(district_key: DistrictKey) -> Response:
    district = District.get_by_id(district_key)
    if district is None:
        abort(404)

    district_teams = DistrictTeam.query(
        DistrictTeam.district_key == district.key
    ).fetch(5000)
    DistrictTeamManipulator.delete(district_teams)
    DistrictManipulator.delete(district)

    return redirect(url_for("admin.district_list", year=district.year))
