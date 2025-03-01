from datetime import datetime, timedelta
from typing import Optional, Sequence

from pytz import timezone, UTC

from backend.common.models.keys import Year
from backend.common.queries.event_query import EventListQuery, LastSeasonEventQuery
from backend.common.sitevars.apistatus import ApiStatus

EST = timezone("US/Eastern")


class SeasonHelper(object):
    """General season-information helper methods"""

    MIN_YEAR: Year = 1992
    MIN_DISTRICT_YEAR: Year = 2009
    MIN_REGIONAL_CMP_POOL_YEAR: Year = 2025

    @staticmethod
    def get_max_year() -> Year:
        status_sv = ApiStatus.get()
        return status_sv["max_season"]

    @staticmethod
    def get_current_season() -> Year:
        status_sv = ApiStatus.get()
        return status_sv["current_season"]

    @classmethod
    def get_valid_years(cls) -> Sequence[Year]:
        max_year = cls.get_max_year()
        return range(cls.MIN_YEAR, max_year + 1)

    @classmethod
    def get_valid_district_years(cls) -> Sequence[Year]:
        max_year = cls.get_max_year()
        return range(cls.MIN_DISTRICT_YEAR, max_year + 1)

    @classmethod
    def get_valid_regional_pool_years(cls) -> Sequence[Year]:
        max_year = cls.get_max_year()
        return range(cls.MIN_REGIONAL_CMP_POOL_YEAR, max_year + 1)

    @classmethod
    def is_valid_regional_pool_year(cls, year: Year) -> bool:
        return year >= cls.MIN_REGIONAL_CMP_POOL_YEAR

    @staticmethod
    def effective_season_year(date=datetime.now()) -> Year:
        """
        Given a date, find the "effective season" year for the date. If all official events have been played, it's
        effectively next season.
        """
        effective_season_year = date.year
        last_event_end_date = None

        last_event = LastSeasonEventQuery(year=effective_season_year).fetch()
        if last_event:
            last_event_end_date = last_event.end_date

        if last_event_end_date is None:
            # No events for year - assume current year is effective season year
            return effective_season_year

        if date > last_event_end_date:
            # All events for current season have been played - effective season is next year
            return effective_season_year + 1
        return effective_season_year

    @staticmethod
    def is_kickoff_at_least_one_day_away(
        date=datetime.now(UTC), year: Year = datetime.now().year
    ) -> bool:
        """
        Returns True if Kickoff for a given year is at least one day away from the current date.
        This will always be True if Kickoff for a given year happened before the current date.
        Ex: SeasonHelper.is_kickoff_at_least_one_day_away(1992) == True
        """
        kickoff_date = SeasonHelper.kickoff_datetime_utc(year)
        return date >= (kickoff_date - timedelta(days=1))

    @staticmethod
    def kickoff_datetime_est(year: Year = datetime.now().year) -> datetime:
        """Computes the date of Kickoff for a given year. Kickoff is always the first Saturday in January after Jan 2nd."""
        jan_2nd = datetime(
            year=year, month=1, day=2, hour=10, minute=30, second=00, tzinfo=EST
        )
        # Since 2021, Kickoff starts at 12:00am EST
        if year >= 2021:
            jan_2nd = jan_2nd.replace(hour=12, minute=00)
        days_ahead = 5 - jan_2nd.weekday()  # Saturday is 5
        # Kickoff won't occur *on* Jan 2nd if it's a Saturday - it'll be the next Saturday
        if days_ahead <= 0:
            days_ahead += 7
        return jan_2nd + timedelta(days=days_ahead)

    @staticmethod
    def kickoff_datetime_utc(year: Year = datetime.now().year) -> datetime:
        """Converts kickoff_date to a UTC datetime"""
        return SeasonHelper.kickoff_datetime_est(year).astimezone(UTC)

    @staticmethod
    def first_event_datetime_utc(
        year: Year = datetime.now().year,
    ) -> Optional[datetime]:
        """Computes day the first in-season event begins"""
        events = EventListQuery(year).fetch()
        earliest_start = None
        for event in events:
            if event.is_in_season and (
                earliest_start is None or event.start_date < earliest_start
            ):
                earliest_start = event.start_date
        return earliest_start
