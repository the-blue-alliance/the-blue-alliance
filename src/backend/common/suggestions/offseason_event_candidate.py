from datetime import datetime
from typing import Optional

from backend.common.consts.event_type import EventType
from backend.common.models.event import Event
from backend.common.models.suggestion import Suggestion


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def candidate_event_from_suggestion(suggestion: Suggestion) -> Event:
    """
    The Event an offseason-event suggestion describes, as an unsaved model.

    Both review surfaces -- the Jinja review page and the moderation API behind
    the PWA -- compare this candidate against existing events to surface
    returning events under new names, so they must build it the same way.
    """
    contents = suggestion.contents
    start_date = _parse_date(contents.get("start_date"))
    end_date = _parse_date(contents.get("end_date"))
    venue = contents.get("venue_name")
    city = contents.get("city")
    state = contents.get("state")
    country = contents.get("country")
    event_type = contents.get("event_type", EventType.OFFSEASON)
    return Event(
        end_date=end_date,
        event_type_enum=event_type or EventType.OFFSEASON,
        district_key=None,
        venue=venue,
        city=city,
        state_prov=state,
        country=country,
        venue_address="{}\n{}\n{}, {}, {}".format(
            venue, contents.get("address"), city, state, country
        ),
        name=contents.get("name"),
        start_date=start_date,
        website=contents.get("website"),
        year=start_date.year if start_date else None,
        first_code=contents.get("first_code", None),
        official=False,
    )
