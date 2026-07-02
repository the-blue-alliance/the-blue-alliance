from flask import redirect
from werkzeug.wrappers import Response

from backend.common.consts.renamed_districts import ALL_KNOWN_DISTRICT_ABBREVIATIONS
from backend.common.models.keys import DistrictAbbreviation, EventKey


def short_team(team_number: str) -> Response:
    return redirect(f"/team/{int(team_number)}", code=301)


def short_event_or_district(short_key: str) -> Response:
    year = int(short_key[:4])
    suffix: DistrictAbbreviation = short_key[4:]

    if suffix in ALL_KNOWN_DISTRICT_ABBREVIATIONS:
        return redirect(f"/events/{suffix}/{year}", code=301)

    event_key: EventKey = short_key
    return redirect(f"/event/{event_key}", code=301)
