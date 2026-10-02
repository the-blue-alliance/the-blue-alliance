from datetime import datetime
from typing import List, Optional

from flask import abort, redirect, request, url_for
from google.appengine.ext import ndb
from werkzeug import Response

from backend.common.consts.webcast_type import WebcastType
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.helpers.youtube_video_helper import YouTubeVideoHelper
from backend.common.manipulators.district_manipulator import DistrictManipulator
from backend.common.manipulators.district_team_manipulator import (
    DistrictTeamManipulator,
)
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.keys import DistrictKey, EventKey, Year
from backend.common.models.team import Team
from backend.common.models.webcast import WebcastChannel
from backend.web.profiled_render import render_template


def district_list(year: Optional[Year]) -> str:
    if not year:
        year = datetime.now().year

    districts = District.query(District.year == year).fetch(10000)
    district_has_youtube_channel = {
        district.abbreviation: any(
            channel.get("type") == WebcastType.YOUTUBE
            and bool(channel.get("channel_id"))
            for channel in (district.webcast_channels or [])
        )
        for district in districts
    }

    template_values = {
        "valid_years": reversed(SeasonHelper.get_valid_district_years()),
        "selected_year": year,
        "districts": districts,
        "district_has_youtube_channel": district_has_youtube_channel,
    }

    return render_template("admin/district_list.html", template_values)


def district_details(district_key: DistrictKey) -> str:
    district = District.get_by_id(district_key)
    if not district:
        abort(404)

    events = Event.query(Event.district_key == district.key).fetch_async()
    api_keys = ApiAuthAccess.query(
        ApiAuthAccess.district_list == ndb.Key(District, district_key)
    ).fetch_async()
    district_teams_future = DistrictTeam.query(
        DistrictTeam.district_key == ndb.Key(District, district_key)
    ).fetch_async()
    district_has_youtube_channel = any(
        channel.get("type") == WebcastType.YOUTUBE and bool(channel.get("channel_id"))
        for channel in (district.webcast_channels or [])
    )

    # Build team -> home_dcmp_event_key mapping for display
    district_teams = district_teams_future.get_result()
    home_dcmp_assignments = [
        (dt.team.id(), dt.home_dcmp_event_key)
        for dt in sorted(district_teams, key=lambda dt: dt.team.id())
        if dt.home_dcmp_event_key
    ]

    template_values = {
        "district": district,
        "events": events.get_result(),
        "write_auths": api_keys.get_result(),
        "configured_webcast_channels": district.webcast_channels or [],
        "district_has_youtube_channel": district_has_youtube_channel,
        "webcast_success": request.args.get("webcast_success"),
        "webcast_error": request.args.get("webcast_error"),
        "home_dcmp_success": request.args.get("home_dcmp_success"),
        "home_dcmp_error": request.args.get("home_dcmp_error"),
        "home_dcmp_assignments": home_dcmp_assignments,
    }
    return render_template("admin/district_details.html", template_values)


def district_add_webcast_channel_post(district_key: DistrictKey) -> Response:
    district = District.get_by_id(district_key)
    if not district:
        abort(404)

    channel_name = (request.form.get("channel_name") or "").strip()
    if not channel_name:
        return redirect(
            f"{url_for('admin.district_details', district_key=district_key, webcast_error='missing_channel_name')}#webcasts"
        )

    resolved_channel = YouTubeVideoHelper.resolve_channel_id(channel_name).get_result()
    if not resolved_channel:
        return redirect(
            f"{url_for('admin.district_details', district_key=district_key, webcast_error='channel_not_found')}#webcasts"
        )

    district_channels = list(district.webcast_channels or [])

    if any(
        channel["channel_id"] == resolved_channel["channel_id"]
        for channel in district_channels
    ):
        return redirect(
            f"{url_for('admin.district_details', district_key=district_key, webcast_error='channel_exists')}#webcasts"
        )

    district_channels.append(
        WebcastChannel(
            type=WebcastType.YOUTUBE,
            channel=resolved_channel["channel_name"],
            channel_id=resolved_channel["channel_id"],
        )
    )
    district.webcast_channels = district_channels
    DistrictManipulator.createOrUpdate(district)

    return redirect(
        f"{url_for('admin.district_details', district_key=district_key, webcast_success='channel_added')}#webcasts"
    )


def district_remove_webcast_channel_post(district_key: DistrictKey) -> Response:
    district = District.get_by_id(district_key)
    if not district:
        abort(404)

    channel_id = (request.form.get("channel_id") or "").strip()
    if not channel_id:
        return redirect(
            f"{url_for('admin.district_details', district_key=district_key, webcast_error='missing_channel_id')}#webcasts"
        )

    district_channels = list(district.webcast_channels or [])
    original_count = len(district_channels)

    district_channels = [
        channel
        for channel in district_channels
        if channel.get("channel_id") != channel_id
    ]

    if len(district_channels) == original_count:
        return redirect(
            f"{url_for('admin.district_details', district_key=district_key, webcast_error='channel_not_found_to_remove')}#webcasts"
        )

    district.webcast_channels = district_channels
    DistrictManipulator.createOrUpdate(district)

    return redirect(
        f"{url_for('admin.district_details', district_key=district_key, webcast_success='channel_removed')}#webcasts"
    )


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
    uses_official_webcast_unit = request.form.get("uses_official_webcast_unit") == "on"

    if district_key is None:
        district_key = District.render_key_name(year, abbreviation)

    if not District.validate_key_name(district_key):
        abort(400)

    district = District(
        id=district_key,
        year=year,
        abbreviation=abbreviation,
        display_name=display_name,
        uses_official_webcast_unit=uses_official_webcast_unit,
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


def district_set_home_dcmp_post(district_key: DistrictKey) -> Response:
    """
    Accepts a CSV of "team_number,event_code" lines and sets the
    home_dcmp_event_key on each team's DistrictTeam record.
    """
    district = District.get_by_id(district_key)
    if not district:
        abort(404)

    csv_data = (request.form.get("csv_data") or "").strip()
    to_update: List[DistrictTeam] = []
    errors: List[str] = []

    for raw_line in csv_data.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 2:
            errors.append(f"Invalid line (expected team,event_code): {line}")
            continue

        team_part, event_code = parts[0], parts[1].lower()
        if team_part.startswith("frc"):
            team_key = team_part
        else:
            try:
                team_key = f"frc{int(team_part)}"
            except ValueError:
                errors.append(f"Invalid team number: {team_part}")
                continue

        home_dcmp_event_key: EventKey = f"{district.year}{event_code}"
        dt_id = DistrictTeam.render_key_name(district_key, team_key)
        existing = DistrictTeam.get_by_id(dt_id)
        if existing is None:
            errors.append(f"No DistrictTeam found for {team_key} in {district_key}")
            continue

        # Build a new object so updateMerge picks up home_dcmp_event_key
        new_dt = DistrictTeam(
            id=dt_id,
            team=ndb.Key(Team, team_key),
            district_key=ndb.Key(District, district_key),
            year=district.year,
            home_dcmp_event_key=home_dcmp_event_key,
        )
        to_update.append(new_dt)

    if to_update:
        for dt in to_update:
            DistrictTeamManipulator.createOrUpdate(dt)

    error_param = "||".join(errors) if errors else None
    success_param = str(len(to_update)) if to_update else None
    redirect_url = url_for(
        "admin.district_details",
        district_key=district_key,
        home_dcmp_success=success_param,
        home_dcmp_error=error_param,
    )
    return redirect(f"{redirect_url}#home_dcmp")
