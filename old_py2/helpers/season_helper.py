from calendar import monthrange
from datetime import datetime, timedelta, tzinfo, date
from google.appengine.ext import ndb
from pytz import timezone, UTC

from consts.event_type import EventType
from models.event import Event


EST = timezone('EST')


class SeasonHelper:
    """ General season-information helper methods """

    @staticmethod
    def effective_season_year(date=datetime.now()):
        """
        Given a date, find the "effective season" year for the date. If all official events have been played, it's
        effectively next season.
        """
        effective_season_year = date.year
        last_event_end_date = None

        last_event_list = Event.query(
            Event.year==int(date.year),
            Event.event_type_enum.IN(EventType.SEASON_EVENT_TYPES)
        ).order(-Event.end_date).fetch(1, projection=[Event.end_date])
        if last_event_list:
            last_event = last_event_list[0]
            last_event_end_date = last_event.end_date

        if last_event_end_date is None:
            # No events for year - assume current year is effective season year
            return effective_season_year

        if date > last_event_end_date:
            # All events for current season have been played - effective season is next year
            return effective_season_year + 1
        return effective_season_year

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
    def first_event_datetime_utc(year=datetime.now().year):
        """ Computes day the first in-season event begins """
        from database import event_query
        events = event_query.EventListQuery(year).fetch()
        earliest_start = None
        timezone = None
        for event in events:
            if event.is_season_event and (earliest_start is None or event.start_date < earliest_start):
                earliest_start = event.start_date
                timezone = event.timezone_id
        return earliest_start
