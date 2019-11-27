from mock import patch
import unittest2
from datetime import datetime, timedelta
from pytz import timezone, UTC

from helpers.season_helper import SeasonHelper


class TestSeasonHelper(unittest2.TestCase):

    def test_is_kickoff_at_least_one_day_away(self):
        a = datetime(2020, 1, 3, 14, 30, 00, tzinfo=UTC)  # False - over one day
        b = datetime(2020, 1, 3, 15, 30, 00, tzinfo=UTC)  # True - exactly one day
        c = datetime(2020, 1, 4, 15, 30, 00, tzinfo=UTC)  # True - same time
        d = datetime(2020, 2, 4, 15, 30, 00, tzinfo=UTC)  # True - very far away in the future
        expected_results = [False, True, True, True]

        for (date, result) in zip([a, b, c, d], expected_results):
            at_least_one_day_away = SeasonHelper.is_kickoff_at_least_one_day_away(date, 2020)
            self.assertEqual(at_least_one_day_away, result)

    def test_kickoff_datetime(self):
        # 2011 - Saturday the 8th (https://en.wikipedia.org/wiki/Logo_Motion)
        kickoff_2011 = datetime(2011, 1, 8, 10, 30, 00, tzinfo=timezone('EST'))
        kickoff_2011_utc = kickoff_2011.astimezone(UTC)
        self.assertEqual(SeasonHelper.kickoff_datetime_est(year=2011), kickoff_2011)
        self.assertEqual(SeasonHelper.kickoff_datetime_utc(year=2011), kickoff_2011_utc)
        # 2010 - Saturday the 9th (https://en.wikipedia.org/wiki/Breakaway_(FIRST))
        kickoff_2010 = datetime(2010, 1, 9, 10, 30, 00, tzinfo=timezone('EST'))
        kickoff_2010_utc = kickoff_2010.astimezone(UTC)
        self.assertEqual(SeasonHelper.kickoff_datetime_est(year=2010), kickoff_2010)
        self.assertEqual(SeasonHelper.kickoff_datetime_utc(year=2010), kickoff_2010_utc)
        # 2009 - Saturday the 3rd (https://en.wikipedia.org/wiki/Lunacy_(FIRST)
        kickoff_2009 = datetime(2009, 1, 3, 10, 30, 00, tzinfo=timezone('EST'))
        kickoff_2009_utc = kickoff_2009.astimezone(UTC)
        self.assertEqual(SeasonHelper.kickoff_datetime_est(year=2009), kickoff_2009)
        self.assertEqual(SeasonHelper.kickoff_datetime_utc(year=2009), kickoff_2009_utc)

    def test_stop_build_date(self):
        # 2019 - Feb 19th, 2019
        stop_build_2019 = datetime(2019, 2, 19, 23, 59, 59, tzinfo=timezone('EST'))
        stop_build_2019_utc = stop_build_2019.astimezone(UTC)
        self.assertEqual(SeasonHelper.stop_build_datetime_est(year=2019), stop_build_2019)
        self.assertEqual(SeasonHelper.stop_build_datetime_utc(year=2019), stop_build_2019_utc)
        # 2018 - Feb 20th, 2018
        stop_build_2018 = datetime(2018, 2, 20, 23, 59, 59, tzinfo=timezone('EST'))
        stop_build_2018_utc = stop_build_2018.astimezone(UTC)
        self.assertEqual(SeasonHelper.stop_build_datetime_est(year=2018), stop_build_2018)
        self.assertEqual(SeasonHelper.stop_build_datetime_utc(year=2018), stop_build_2018_utc)
        # 2017 - Feb 21th, 2017
        stop_build_2017 = datetime(2017, 2, 21, 23, 59, 59, tzinfo=timezone('EST'))
        stop_build_2017_utc = stop_build_2017.astimezone(UTC)
        self.assertEqual(SeasonHelper.stop_build_datetime_est(year=2017), stop_build_2017)
        self.assertEqual(SeasonHelper.stop_build_datetime_utc(year=2017), stop_build_2017_utc)
        # 2016 - Feb 23th, 2016
        stop_build_2016 = datetime(2016, 2, 23, 23, 59, 59, tzinfo=timezone('EST'))
        stop_build_2016_utc = stop_build_2016.astimezone(UTC)
        self.assertEqual(SeasonHelper.stop_build_datetime_est(year=2016), stop_build_2016)
        self.assertEqual(SeasonHelper.stop_build_datetime_utc(year=2016), stop_build_2016_utc)
