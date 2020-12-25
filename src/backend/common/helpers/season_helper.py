from datetime import datetime, timedelta
from typing import Iterable

from pytz import timezone, UTC

from backend.common.models.keys import Year
from backend.common.sitevars.apistatus import ApiStatus

EST = timezone("EST")


class SeasonHelper(object):

    MIN_YEAR: Year = 1992

    @staticmethod
    def get_max_year() -> Year:
        status_sv = ApiStatus.get()
        return status_sv["max_season"]

    @staticmethod
    def get_current_season() -> Year:
        status_sv = ApiStatus.get()
        return status_sv["current_season"]

    @classmethod
    def get_valid_years(cls) -> Iterable[Year]:
        max_year = cls.get_max_year()
        return range(cls.MIN_YEAR, max_year + 1)

    @staticmethod
    def kickoff_datetime_est(year: int = datetime.now().year) -> datetime:
        """ Computes the date of Kickoff for a given year. Kickoff is always the first Saturday in January after Jan 2nd. """
        jan_2nd = datetime(year, 1, 2, 10, 30, 00, tzinfo=EST)
        # Since 2021, Kickoff starts at 12:00am EST
        if year >= 2021:
            jan_2nd = jan_2nd.replace(hour=12, minute=00)
        days_ahead = 5 - jan_2nd.weekday()  # Saturday is 5
        # Kickoff won't occur *on* Jan 2nd if it's a Saturday - it'll be the next Saturday
        if days_ahead <= 0:
            days_ahead += 7
        return jan_2nd + timedelta(days=days_ahead)

    @staticmethod
    def kickoff_datetime_utc(year: int = datetime.now().year) -> datetime:
        """ Converts kickoff_date to a UTC datetime """
        return SeasonHelper.kickoff_datetime_est(year).astimezone(UTC)
