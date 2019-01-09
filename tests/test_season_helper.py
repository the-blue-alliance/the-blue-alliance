import unittest2
from datetime import date, datetime

from helpers.season_helper import SeasonHelper


class TestSeasonHelper(unittest2.TestCase):

    def test_kickoff_date(self):
        # 2011 - Saturday the 8th (https://en.wikipedia.org/wiki/Logo_Motion)
        kickoff_2011 = date(2011, 1, 8)
        self.assertEqual(SeasonHelper.kickoff_date(year=2011), kickoff_2011)
        # 2010 - Saturday the 9th (https://en.wikipedia.org/wiki/Breakaway_(FIRST))
        kickoff_2010 = date(2010, 1, 9)
        self.assertEqual(SeasonHelper.kickoff_date(year=2010), kickoff_2010)
        # 2009 - Saturday the 3rd (https://en.wikipedia.org/wiki/Lunacy_(FIRST)
        kickoff_2009 = date(2009, 1, 3)
        self.assertEqual(SeasonHelper.kickoff_date(year=2009), kickoff_2009)

    def test_stop_build_date(self):
        # 2019 - Feb 19th, 2019
        stop_build_2019 = datetime(2019, 2, 19, 23, 59, 59)
        self.assertEqual(SeasonHelper.stop_build_date(year=2019), stop_build_2019)
        # 2018 - Feb 20th, 2018
        stop_build_2018 = datetime(2018, 2, 20, 23, 59, 59)
        self.assertEqual(SeasonHelper.stop_build_date(year=2018), stop_build_2018)
        # 2017 - Feb 21th, 2017
        stop_build_2017 = datetime(2017, 2, 21, 23, 59, 59)
        self.assertEqual(SeasonHelper.stop_build_date(year=2017), stop_build_2017)
        # 2016 - Feb 23th, 2016
        stop_build_2016 = datetime(2016, 2, 23, 23, 59, 59)
        self.assertEqual(SeasonHelper.stop_build_date(year=2016), stop_build_2016)
