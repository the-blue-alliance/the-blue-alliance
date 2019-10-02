from datetime import datetime, timedelta, tzinfo
from pytz import timezone, UTC


EST = timezone('EST')


class SeasonHelper:
    """ General season-information helper methods """

    @staticmethod
    def is_kickoff_at_least_one_day_away(date=datetime.now(UTC), year=datetime.now().year):
        """
        Returns True if Kickoff for a given year is at least one day away from the current date.
        This will always be True if Kickoff for a given year happened before the current date.
        Ex: SeasonHelper.is_kickoff_at_least_one_day_away(1992) == True
        """
        kickoff_date = SeasonHelper.kickoff_datetime_utc(year)
        return date >= (kickoff_date - timedelta(days=1))

    @staticmethod
    def kickoff_datetime_est(year=datetime.now().year):
        """ Computes the date of Kickoff for a given year. Kickoff is always the first Saturday in January after Jan 2nd. """
        jan_2nd = datetime(year, 1, 2, 10, 30, 00, tzinfo=EST)  # Start Kickoff at 10:30am EST
        days_ahead = 5 - jan_2nd.weekday()  # Saturday is 5
        # Kickoff won't occur *on* Jan 2nd if it's a Saturday - it'll be the next Saturday
        if days_ahead <= 0:
            days_ahead += 7
        return jan_2nd + timedelta(days=days_ahead)

    @staticmethod
    def kickoff_datetime_utc(year=datetime.now().year):
        """ Converts kickoff_date to a UTC datetime """
        return SeasonHelper.kickoff_datetime_est(year).astimezone(UTC)

    @staticmethod
    def stop_build_datetime_est(year=datetime.now().year):
        """ Computes day teams are done working on robots. The stop build day is kickoff + 6 weeks + 3 days. Set to 23:59:59 """
        stop_build_date = datetime.combine(SeasonHelper.kickoff_datetime_est(year).date() + timedelta(days=4, weeks=6), datetime.min.time()) - timedelta(seconds=1)
        return EST.localize(stop_build_date)  # Make our timezone unaware datetime timezone aware

    @staticmethod
    def stop_build_datetime_utc(year=datetime.now().year):
        """ Converts stop_build_date to a UTC datetime """
        return SeasonHelper.stop_build_datetime_est(year).astimezone(UTC)
