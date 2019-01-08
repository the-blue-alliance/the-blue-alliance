from datetime import date, datetime, timedelta


class SeasonHelper:
    """ General season-information helper methods """

    @staticmethod
    def kickoff_date(year=datetime.now().year):
        """ Computes the date of Kickoff for a given year. Kickoff is always the first Saturday in January after Jan 2nd. """
        jan_2nd = date(year, 1, 2)
        days_ahead = 5 - jan_2nd.weekday()  # Saturday is 5
        # Kickoff won't occur *on* Jan 2nd if it's a Saturday - it'll be the next Saturday
        if days_ahead <= 0:
            days_ahead += 7
        return jan_2nd + timedelta(days=days_ahead)

    @staticmethod
    def stop_build_date(year=datetime.now().year):
        """ Computes day teams are done working on robots. The stop build day is kickoff + 6 weeks + 3 days. Set to 23:59:59 """
        return datetime.combine(SeasonHelper.kickoff_date(year=year) + timedelta(days=4, weeks=6), datetime.min.time()) - timedelta(seconds=1)
