import csv
import io
from collections import defaultdict
from typing import Optional

from flask import Blueprint, url_for
from google.appengine.api import taskqueue
from google.cloud import ndb

from backend.common import storage
from backend.common.consts.media_type import SOCIAL_TYPES as MEDIA_TYPE_SOCIAL_TYPES
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
from backend.common.models.media import Media
from backend.common.models.team import Team


blueprint = Blueprint("backup", __name__, url_prefix="/backup")


@blueprint.route("/enqueue")
def backup_enqueue():
    taskqueue.add(
        queue_name="backups", url=url_for("backup.backup_csv_events"), method="GET"
    )
    taskqueue.add(
        queue_name="backups", url=url_for("backup.backup_csv_teams"), method="GET"
    )
    # TODO: Dump backups to GitHub
    return "Enqueued backup for all events and all teams"


@blueprint.route("/events")
@blueprint.route("/events/<int:year>")
def backup_csv_events(year: Optional[int] = None):
    if year is None:
        years = SeasonHelper.get_valid_years()
        for year in years:
            taskqueue.add(
                queue_name="backups",
                url=url_for("backup.backup_csv_events", year=year),
                method="GET",
            )
        years_string = ", ".join([str(y) for y in years])
        return f"Enqueued backup for years: {years_string}"
    else:
        event_keys = Event.query(Event.year == int(year)).fetch(keys_only=True)
        for event_key in event_keys:
            taskqueue.add(
                queue_name="backups",
                url=url_for("backup.backup_csv_event", event_key=event_key.string_id()),
                method="GET",
            )
        return f"Backed up for {len(event_keys)} events: {event_keys}"


@blueprint.route("/event/<event_key>")
def backup_csv_event(event_key: EventKey):
    event = Event.get_by_id(event_key)
    if not event:
        return (f"Cannot backup event for key {event_key} - event not found", 404)

    event.prep_awards_matches_teams()

    PATH_PATTERN = f"tba-data-backup/events/{event.year}/{event_key}"

    if event.awards:
        output = io.StringIO()
        writer = csv.writer(output)

        for award in event.awards:
            for recipient in award.recipient_list:
                team = recipient["team_number"]
                writer.writerow(
                    [award.key.string_id(), award.name_str, f"frc{team}", recipient["awardee"]]
                )

        storage.write(PATH_PATTERN + f"/{event_key}_awards.csv", output.getvalue())
        output.close()

    if event.matches:
        output = io.StringIO()
        writer = csv.writer(output)

        for match in event.matches:
            red_score = match.alliances["red"]["score"]
            blue_score = match.alliances["blue"]["score"]
            # TODO: Can we dump the match game info here too?
            writer.writerow(
                [match.key.string_id()]
                + match.alliances["red"]["teams"]
                + match.alliances["blue"]["teams"]
                + [red_score, blue_score]
            )

        storage.write(PATH_PATTERN + f"/{event_key}_matches.csv", output.getvalue())
        output.close()

    if event.teams:
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([team.key.string_id() for team in event.teams])

        storage.write(PATH_PATTERN + f"/{event_key}_teams.csv", output.getvalue())
        output.close()

    if event.rankings:
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([ranking for ranking in event.rankings])

        storage.write(PATH_PATTERN + f"/{event_key}_rankings.csv", output.getvalue())
        output.close()

    if event.alliance_selections:
        output = io.StringIO()
        writer = csv.writer(output)

        for alliance in event.alliance_selections:
            writer.writerow(alliance["picks"])

        storage.write(PATH_PATTERN + f"/{event_key}_alliances.csv", output.getvalue())
        output.close()

    return f"Done backing up {event_key}!"


@blueprint.route("/teams")
def backup_csv_teams():
    team_keys_future = Team.query().order(Team.team_number).fetch_async(keys_only=True)
    social_media_keys_future = Media.query(
        Media.year == None  # noqa: E711
    ).fetch_async(keys_only=True)

    team_futures = ndb.get_multi_async(team_keys_future.get_result())
    social_futures = ndb.get_multi_async(social_media_keys_future.get_result())

    socials_by_team = defaultdict(dict)
    for social_future in social_futures:
        social = social_future.get_result()
        for reference in social.references:
            socials_by_team[reference.string_id()][social.media_type_enum] = social

    if team_futures:
        output = io.StringIO()
        writer = csv.writer(output)

        for team_future in team_futures:
            team = team_future.get_result()
            # TODO: Note to Zach - do a second pass and make sure we're backing up as much data as possible
            team_row = [
                team.key.string_id(),
                team.nickname,
                team.name,
                team.city,
                team.state_prov,
                team.country,
                team.website,
                team.rookie_year,
            ]
            for social_type in MEDIA_TYPE_SOCIAL_TYPES:
                social = socials_by_team[team.key.string_id()].get(social_type, None)
                team_row.append(
                    social.social_profile_url if social is not None else None
                )

            writer.writerow(team_row)

        storage.write("tba-data-backup/teams/teams.csv", output.getvalue())
        output.close()

    return f"Exported {len(team_futures)} teams to CSV"
