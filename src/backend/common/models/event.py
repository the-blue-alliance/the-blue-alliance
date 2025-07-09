from __future__ import annotations

import datetime
import json
import re
import typing
from typing import Any, cast, Dict, Generator, List, Optional, Set

from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.consts import event_type
from backend.common.consts.event_type import (
    CMP_EVENT_TYPES,
    EventType,
    SEASON_EVENT_TYPES,
)
from backend.common.consts.playoff_type import PlayoffType
from backend.common.futures import TypedFuture
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.alliance import EventAlliance
from backend.common.models.cached_model import CachedModel
from backend.common.models.district import District
from backend.common.models.event_details import EventDetails
from backend.common.models.event_district_points import EventDistrictPoints
from backend.common.models.event_playoff_advancement import (
    TBracketTable,
    TPlayoffAdvancement,
)
from backend.common.models.event_ranking import EventRanking
from backend.common.models.keys import EventKey, TeamKey, Year
from backend.common.models.location import Location
from backend.common.models.webcast import Webcast, WebcastOnlineStatus
from backend.common.tasklets import typed_toplevel

if typing.TYPE_CHECKING:
    from backend.common.models.award import Award
    from backend.common.models.match import Match
    from backend.common.models.team import Team


class Event(CachedModel):
    """
    Events represent FIRST Robotics Competition events, both official and unofficial.
    key_name is like '2010ct'
    """

    EVENT_SHORT_EXCEPTIONS = {
        "arc": "archimedes",
        "cars": "carson",
        "carv": "carver",
        "cur": "curie",
        "dal": "daly",
        "dar": "darwin",
        "gal": "galileo",
        "hop": "hopper",
        "new": "newton",
        "roe": "roebling",
        "tes": "tesla",
        "tur": "turing",
        "joh": "johnson",
        "mil": "milstein",
    }

    EVENT_SHORT_EXCEPTIONS_2023 = {
        "arc": "arpky",
        "cur": "cpra",
        "dal": "dcmp",
        "gal": "gcmp",
        "hop": "hcmp",
        "joh": "jcmp",
        "mil": "mpcia",
        "new": "npfcmp",
    }

    name = ndb.StringProperty()
    event_type_enum = ndb.IntegerProperty(required=True, choices=list(EventType))

    # Should not contain "Regional" or "Division", like "Hartford"
    short_name = ndb.TextProperty(indexed=False)
    event_short = ndb.TextProperty(
        required=True, indexed=False
    )  # Smaller abbreviation like "CT"
    first_code = (
        ndb.StringProperty()
    )  # Event code used in FIRST's API, if different from event_short
    year: Year = ndb.IntegerProperty(required=True)
    district_key: Optional[ndb.Key] = ndb.KeyProperty(kind=District)
    start_date = ndb.DateTimeProperty()
    end_date = ndb.DateTimeProperty()
    playoff_type: PlayoffType = cast(
        PlayoffType, ndb.IntegerProperty(choices=list(PlayoffType))
    )

    # venue, venue_addresss, city, state_prov, country, and postalcode are from FIRST
    venue = ndb.TextProperty(indexed=False)  # Name of the event venue
    venue_address = ndb.TextProperty(
        indexed=False
    )  # Most detailed venue address (includes venue, street, and location separated by \n)
    city = ndb.StringProperty()  # Equivalent to locality. From FRCAPI
    state_prov = ndb.StringProperty()  # Equivalent to region. From FRCAPI
    country = ndb.StringProperty()  # From FRCAPI
    postalcode = (
        ndb.StringProperty()
    )  # From ElasticSearch only. String because it can be like "95126-1215"
    # Normalized address from the Google Maps API, constructed using the above
    normalized_location: Optional[Location] = cast(
        Location, ndb.StructuredProperty(Location)
    )

    timezone_id = (
        ndb.StringProperty()
    )  # such as 'America/Los_Angeles' or 'Asia/Jerusalem'
    official: bool = ndb.BooleanProperty(default=False)  # Is the event FIRST-official?
    first_eid = ndb.StringProperty()  # from USFIRST
    parent_event: Optional[ndb.Key] = (
        ndb.KeyProperty()
    )  # This is the division -> event champs relationship
    # event champs -> all divisions
    divisions: List[ndb.Key] = ndb.KeyProperty(repeated=True)  # pyre-ignore[8]
    facebook_eid = ndb.TextProperty(indexed=False)  # from Facebook
    custom_hashtag = ndb.TextProperty(indexed=False)  # Custom HashTag
    website = ndb.TextProperty(indexed=False)
    webcast_json: str = ndb.TextProperty(
        indexed=False
    )  # list of dicts, valid keys include 'type' and 'channel'
    enable_predictions = ndb.BooleanProperty(default=False)
    remap_teams: Dict[str, str] = (
        ndb.JsonProperty()
    )  # Map of temporary team numbers to pre-rookie and B teams. key is the old team key, value is the new team key

    created = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated = ndb.DateTimeProperty(auto_now=True, indexed=False)

    _mutable_attrs: Set[str] = {
        "end_date",
        "event_short",
        "event_type_enum",
        "district_key",
        "custom_hashtag",
        "enable_predictions",
        "facebook_eid",
        "first_code",
        "first_eid",
        "city",
        "state_prov",
        "country",
        "postalcode",
        "parent_event",
        "playoff_type",
        "normalized_location",  # Overwrite whole thing as one
        "timezone_id",
        "name",
        "official",
        "short_name",
        "start_date",
        "venue",
        "venue_address",
        "website",
        "year",
        "remap_teams",
    }

    _allow_none_attrs: Set[str] = {
        "district_key",
    }

    _list_attrs: Set[str] = {
        "divisions",
    }

    def __init__(self, *args, **kw):
        # store set of affected references referenced keys for cache clearing
        # keys must be model properties
        self._affected_references = {"key": set(), "year": set(), "district_key": set()}
        self._awards_future: Optional[TypedFuture[List[Award]]] = None
        self._details_future: Optional[TypedFuture[EventDetails]] = None
        self._location = None
        self._city_state_country = None
        self._matches_future: Optional[TypedFuture[List[Match]]] = None
        self._teams_future: Optional[TypedFuture[List[Team]]] = None
        self._venue_address_safe = None
        self._webcast = None
        self._updated_attrs = []  # Used in EventManipulator to track what changed
        self._week = None
        super(Event, self).__init__(*args, **kw)

    @property
    def alliance_selections(self) -> Optional[List[EventAlliance]]:
        if self.details is None:
            return None
        else:
            return self.details.alliance_selections

    @property
    def alliance_teams(self) -> List[TeamKey]:
        # Load a list of team keys playing in elims
        alliances = self.alliance_selections
        if alliances is None:
            return []
        teams = []
        for alliance in alliances:
            for pick in alliance["picks"]:
                teams.append(pick)

            backup = alliance.get("backup")
            if backup is not None:
                teams.append(backup["in"])
        return teams

    def prep_awards(self) -> None:
        if self._awards_future is None:
            from backend.common.queries import award_query

            self._awards_future = award_query.EventAwardsQuery(
                event_key=self.key_name
            ).fetch_async()

    @property
    def awards(self) -> List["Award"]:
        if self._awards_future is None:
            self.prep_awards()
        return none_throws(self._awards_future).get_result()

    def prep_details(self) -> None:
        if self._details_future is None:
            self._details_future = ndb.Key(EventDetails, self.key.id()).get_async()

    @property
    def details(self) -> EventDetails:
        if self._details_future is None:
            self.prep_details()
        if not none_throws(self._details_future).done():
            none_throws(self._details_future).wait()
        return none_throws(self._details_future).get_result()

    @property
    def district_points(self) -> Optional[EventDistrictPoints]:
        if self.details is None:
            return None
        else:
            return self.details.district_points

    @property
    def regional_champs_pool_points(self) -> Optional[EventDistrictPoints]:
        if self.event_type_enum != EventType.REGIONAL or self.details is None:
            return None

        return self.details.regional_champs_pool_points

    @property
    def playoff_advancement(self) -> Optional[TPlayoffAdvancement]:
        if self.details is None:
            return None
        else:
            return (
                self.details.playoff_advancement.get("advancement")
                if self.details.playoff_advancement
                else None
            )

    @property
    def playoff_bracket(self) -> Optional[TBracketTable]:
        if self.details is None:
            return None
        else:
            return (
                self.details.playoff_advancement.get("bracket")
                if self.details.playoff_advancement
                else None
            )

    def clear_matches(self) -> None:
        self._matches_future = None

    def clear_awards(self) -> None:
        self._awards_future = None

    def clear_teams(self) -> None:
        self._teams_future = None

    def prep_matches(self) -> None:
        if self._matches_future is None:
            from backend.common.queries import match_query

            self._matches_future = match_query.EventMatchesQuery(
                event_key=self.key_name
            ).fetch_async()

    @property
    def matches(self) -> List["Match"]:
        if self._matches_future is None:
            self.prep_matches()
        return none_throws(self._matches_future).get_result()

    def time_as_utc(self, time: datetime.datetime) -> datetime.datetime:
        import pytz

        if self.timezone_id is not None:
            tz = pytz.timezone(self.timezone_id)
            try:
                time = time - none_throws(tz.utcoffset(time))
            except (
                pytz.NonExistentTimeError,
                pytz.AmbiguousTimeError,
            ):  # may happen during DST
                time = time - none_throws(
                    tz.utcoffset(time + datetime.timedelta(hours=1))
                )  # add offset to get out of non-existant time
        return time

    def local_time(self) -> datetime.datetime:
        import pytz

        now = datetime.datetime.now()
        if self.timezone_id is not None:
            tz = pytz.timezone(self.timezone_id)
            try:
                now = now + none_throws(tz.utcoffset(now))
            except (
                pytz.NonExistentTimeError,
                pytz.AmbiguousTimeError,
            ):  # may happen during DST
                now = now + none_throws(
                    tz.utcoffset(now + datetime.timedelta(hours=1))
                )  # add offset to get out of non-existant time
        return now

    def withinDays(self, negative_days_before: int, days_after: int) -> bool:
        if not self.start_date or not self.end_date:
            return False
        now = self.local_time()
        after_start = (
            self.start_date.date() + datetime.timedelta(days=negative_days_before)
            <= now.date()
        )
        before_end = (
            self.end_date.date() + datetime.timedelta(days=days_after) >= now.date()
        )

        return after_start and before_end

    @property
    def now(self) -> bool:
        if self.timezone_id is not None:
            return self.withinDays(0, 0)
        else:
            return self.within_a_day  # overestimate what is "now" if no timezone

    @property
    def within_a_day(self) -> bool:
        return self.withinDays(-1, 1)

    @property
    def past(self) -> bool:
        return self.end_date.date() < self.local_time().date() and not self.now

    @property
    def future(self) -> bool:
        return self.start_date.date() > self.local_time().date() and not self.now

    @property
    def starts_today(self) -> bool:
        return self.start_date.date() == self.local_time().date()

    @property
    def ends_today(self) -> bool:
        return self.end_date.date() == self.local_time().date()

    @property
    def week(self) -> Optional[int]:
        """
        Returns the week of the event relative to the first official season event as an integer
        Returns None if the event is not of type NON_CMP_EVENT_TYPES or is not official
        """
        if (
            self.event_type_enum not in event_type.NON_CMP_EVENT_TYPES
            or not self.official
        ):
            return None

        if self._week:
            return self._week

        # Cache week_start for the same context
        from backend.common.context_cache import context_cache

        cache_key = "{}_season_start".format(self.year)
        season_start = context_cache.get(cache_key)
        if season_start is None:
            e = (
                Event.query(
                    Event.year == self.year,
                    Event.event_type_enum.IN(event_type.NON_CMP_EVENT_TYPES),
                    Event.start_date != None,  # noqa: E711
                )
                .order(Event.start_date)
                .fetch(1, projection=[Event.start_date])
            )
            if e:
                first_start_date = e[0].start_date

                days_diff = 0
                # Before 2018, event weeks start on Wednesdays
                if self.year < 2018:
                    days_diff = 2  # 2 is Wednesday

                # Find the closest start weekday (Monday or Wednesday) to the first event - this is our season start
                diff_from_week_start = (first_start_date.weekday() - days_diff) % 7
                diff_from_week_start = min(
                    [diff_from_week_start, diff_from_week_start - 7],
                    key=lambda x: abs(x),
                )

                season_start = first_start_date - datetime.timedelta(
                    days=diff_from_week_start
                )
            else:
                season_start = None
            context_cache.set(cache_key, season_start)

        if self._week is None and season_start is not None:
            # Round events that occur just before the official start-of-season to the closest week
            days = max((self.start_date - season_start).days, 0)
            self._week = days // 7

        return self._week

    @property
    def week_str(self) -> Optional[str]:
        if self.week is None:
            return None

        week = none_throws(self.week)
        if self.year == 2016:
            return "Week {}".format(0.5 if week == 0 else week)
        elif self.year == 2021:
            # Group 2021 Events by their type - depends on both
            if week == 0:
                return "Participation"
            elif week == 6:
                return "FIRST Innovation Challenge"
            elif week == 7:
                return "INFINITE RECHARGE At Home Challenge"
            elif week == 8:
                return "Game Design Challenge"
            else:
                return "Awards"
        return "Week {}".format(week + 1)

    def prep_teams(self) -> None:
        if self._teams_future is None:
            from backend.common.queries import team_query

            self._teams_future = team_query.EventTeamsQuery(
                event_key=self.key_name
            ).fetch_async()

    @property
    def teams(self) -> List["Team"]:
        if self._teams_future is None:
            self.prep_teams()
        return none_throws(self._teams_future).get_result()

    @property
    def matchstats(self):
        if self.details is None:
            return None
        else:
            return self.details.matchstats

    @property
    def coprs(self):
        if self.details is None:
            return None
        else:
            return self.details.coprs

    @property
    def rankings(self) -> Optional[List[EventRanking]]:
        if self.details is None:
            return None
        else:
            return self.details.rankings2

    @property
    def location(self) -> Optional[str]:
        if self._location is None:
            split_location = []
            if self.city:
                split_location.append(self.city)
            if self.state_prov:
                if self.postalcode:
                    split_location.append(self.state_prov + " " + self.postalcode)
                else:
                    split_location.append(self.state_prov)
            if self.country:
                split_location.append(self.country)
            self._location = ", ".join(split_location)
        return self._location

    @property
    def city_state_country(self) -> Optional[str]:
        if not self._city_state_country:
            location_parts = []
            if self.city:
                location_parts.append(self.city)
            if self.state_prov:
                location_parts.append(self.state_prov)
            if self.country:
                country = self.country
                if self.country == "US":
                    country = "USA"
                location_parts.append(country)
            self._city_state_country = ", ".join(location_parts)
        return self._city_state_country

    @property
    def nl(self) -> Optional[Location]:
        return self.normalized_location

    @property
    def venue_or_venue_from_address(self) -> Optional[str]:
        if self.venue:
            return self.venue
        else:
            try:
                return self.venue_address.split("\r\n")[0]
            except Exception:
                return None

    @property
    def venue_address_safe(self) -> Optional[str]:
        """
        Construct (not detailed) venue address if detailed venue address doesn't exist
        """
        if not self.venue_address:
            if not self.venue or not self.location:
                self._venue_address_safe = None
            else:
                self._venue_address_safe = "{}\n{}".format(
                    none_throws(self.venue).encode("utf-8"),
                    none_throws(self.location).encode("utf-8"),
                )
        else:
            self._venue_address_safe = self.venue_address.replace("\r\n", "\n")
            if self.venue is not None and self.venue not in self._venue_address_safe:
                self._venue_address_safe = "{}\n{}".format(
                    none_throws(self.venue),
                    self._venue_address_safe,
                )
            if (
                self.location is not None
                and self.location not in self._venue_address_safe
            ):
                self._venue_address_safe = "{}\n{}".format(
                    self._venue_address_safe,
                    none_throws(self.location),
                )
        return self._venue_address_safe

    @property
    def webcast(self) -> List[Webcast]:
        """
        Lazy load parsing webcast JSON
        """
        if self._webcast is None:
            try:
                self._webcast: List[Webcast] = json.loads(self.webcast_json)

                # Sort firstinspires channels to the front, keep the order of the rest
                self._webcast = sorted(
                    self._webcast or [],
                    key=lambda w: (
                        0
                        if (
                            w["type"] == "twitch"
                            and w["channel"].startswith("firstinspires")
                        )
                        else 1
                    ),
                )
            except Exception:
                self._webcast = None
        return self._webcast or []

    @typed_toplevel
    def _patch_webcast_online_status(self) -> Generator[Any, Any, None]:
        status_futures = [
            WebcastOnlineStatusMemcache(webcast).get_async()
            for webcast in self.current_webcasts
        ]
        statuses: List[Optional[Webcast]] = yield status_futures

        for webcast, with_status in zip(self.current_webcasts, statuses):
            if with_status is not None:
                webcast.update(
                    WebcastOnlineStatus(
                        status=with_status["status"],
                        stream_title=with_status["stream_title"],
                        viewer_count=with_status["viewer_count"],
                    )
                )

    @property
    def webcast_status(self) -> str:
        self._patch_webcast_online_status()

        overall_status = "offline"
        for webcast_with_status in self.current_webcasts:
            if webcast_with_status is None:
                continue
            status = webcast_with_status.get("status")
            if status == "online":
                overall_status = "online"
                break
            elif status == "unknown":
                overall_status = "unknown"
        return overall_status

    @property
    def current_webcasts(self) -> List[Webcast]:
        if not self.webcast or not self.within_a_day:
            return []

        # Filter by date
        current_webcasts = []
        for webcast in none_throws(self.webcast):
            if "date" in webcast:
                webcast_datetime = datetime.datetime.strptime(
                    webcast["date"], "%Y-%m-%d"
                )
                if self.local_time().date() == webcast_datetime.date():
                    current_webcasts.append(webcast)
            else:
                current_webcasts.append(webcast)
        return current_webcasts

    @property
    def online_webcasts(self):
        self._patch_webcast_online_status()
        current_webcasts = self.current_webcasts
        return list(
            filter(
                lambda x: x.get("status", "") != "offline",
                current_webcasts if current_webcasts else [],
            )
        )

    @property
    def has_first_official_webcast(self) -> bool:
        return (
            any([("firstinspires" in w["channel"]) for w in none_throws(self.webcast)])
            if self.webcast
            else False
        )

    @property
    def division_keys_json(self) -> str:
        keys = [key.id() for key in self.divisions]
        return json.dumps(keys)

    @property
    def key_name(self) -> EventKey:
        """
        Returns the string of the key_name of the Event object before writing it.
        """
        return str(self.year) + self.event_short

    @property
    def facebook_event_url(self) -> str:
        """
        Return a string of the Facebook Event URL.
        """
        return "http://www.facebook.com/event.php?eid=%s" % self.facebook_eid

    @property
    def details_url(self) -> str:
        """
        Returns the URL pattern for the link to this Event on TBA
        """
        return "/event/%s" % self.key_name

    @property
    def gameday_url(self) -> Optional[str]:
        """
        Returns the URL pattern for the link to watch webcasts in Gameday
        """
        if self.webcast:
            return "/gameday/{}".format(self.key_name)
        else:
            return None

    @property
    def public_agenda_url(self) -> Optional[str]:
        if self.event_type_enum not in SEASON_EVENT_TYPES:
            return None

        if self.event_type_enum in CMP_EVENT_TYPES:
            return f"https://www.firstchampionship.org/sites/default/files/{self.year}/{self.year}-FIRST-Robotics-Competition-Addendum.pdf"

        return f"http://firstinspires.org/sites/default/files/uploads/frc/{self.year}-events/{self.year}_{self.event_short.upper()}_Agenda.pdf"

    @property
    def hashtag(self) -> str:
        """
        Return the hashtag used for the event.
        """
        if self.custom_hashtag:
            return self.custom_hashtag
        else:
            return "frc" + self.event_short

    # Depreciated, still here to keep GAE clean.
    webcast_url = ndb.TextProperty(indexed=False)

    @classmethod
    def validate_key_name(cls, event_key: str) -> bool:
        key_name_regex = re.compile(r"^[1-9]\d{3}(\d{2})?[a-z]+[0-9]{0,3}$")
        match = re.match(key_name_regex, event_key)
        return True if match else False

    @property
    def event_district_str(self) -> Optional[str]:
        from backend.common.queries.district_query import DistrictQuery

        if self.district_key is None:
            return None
        district = DistrictQuery(
            district_key=none_throws(none_throws(self.district_key).string_id())
        ).fetch()
        return district.display_name if district else None

    @property
    def event_district_abbrev(self) -> Optional[str]:
        if self.district_key is None:
            return None
        else:
            return none_throws(none_throws(self.district_key).string_id())[4:]

    @property
    def event_district_key(self) -> Optional[str]:
        if self.district_key is None:
            return None
        else:
            return none_throws(none_throws(self.district_key).string_id())

    @property
    def event_type_str(self) -> str:
        return event_type.TYPE_NAMES[EventType(self.event_type_enum)]

    @property
    def display_name(self) -> str:
        return self.name if self.short_name is None else self.short_name

    @property
    def normalized_name(self) -> str:
        if self.event_type_enum == EventType.CMP_FINALS:
            if self.year >= 2017:
                return "{} {}".format(self.city, "Championship")
            else:
                return "Championship"
        elif self.short_name and self.event_type_enum != EventType.FOC:
            if self.event_type_enum == EventType.OFFSEASON:
                return self.short_name
            else:
                return "{} {}".format(
                    self.short_name,
                    event_type.SHORT_TYPE_NAMES[EventType(self.event_type_enum)],
                )
        else:
            return self.name

    @property
    def first_api_code(self) -> str:
        if self.first_code is None:
            return self.compute_first_api_code(self.year, self.event_short)
        return self.first_code

    @classmethod
    def compute_first_api_code(cls, year: int, event_short: str) -> str:
        if year == 2023:
            return cls.EVENT_SHORT_EXCEPTIONS_2023.get(event_short, event_short)
        return cls.EVENT_SHORT_EXCEPTIONS.get(event_short, event_short)

    @property
    def is_in_season(self) -> bool:
        """
        If the Event is of a regular season type.
        """
        return self.event_type_enum in event_type.SEASON_EVENT_TYPES

    @property
    def is_offseason(self) -> bool:
        """
        'Offseason' events include preseason, offseason, unlabeled events.
        """
        return not self.is_in_season

    """
    @property
    def next_match(self):
        from helpers.match_helper import MatchHelper
        upcoming_matches = MatchHelper.upcoming_matches(self.matches, 1)
        if upcoming_matches:
            return upcoming_matches[0]
        else:
            return None

    @property
    def previous_match(self):
        from helpers.match_helper import MatchHelper
        recent_matches = MatchHelper.recent_matches(self.matches, 1)[0]
        if recent_matches:
            return recent_matches[0]
        else:
            return None
    """

    def team_awards(self):
        # Returns a dictionary of awards for teams
        team_awards = {}  # Key is a Team key, value is an array of Awards that team won
        for award in self.awards:
            for team_key in award.team_list:
                a = team_awards.get(team_key, [])
                a.append(award)
                team_awards[team_key] = a
        return team_awards
