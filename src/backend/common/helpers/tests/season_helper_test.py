from datetime import datetime
from backend.common.helpers.season_helper import SeasonHelper

from pytz import timezone, UTC

EST = timezone("EST")


def test_kickoff_datetime() -> None:
    # 2021 - Saturday the 9th, 12:00am EST (https://www.firstinspires.org/robotics/frc/blog/2021-kickoff)
    kickoff_2021 = datetime(2021, 1, 9, 12, 00, 00, tzinfo=EST)
    kickoff_2021_utc = kickoff_2021.astimezone(UTC)
    assert SeasonHelper.kickoff_datetime_est(year=2021) == kickoff_2021
    assert SeasonHelper.kickoff_datetime_utc(year=2021) == kickoff_2021_utc

    # 2020 - Saturday the 4th, 10:30am EST (https://www.firstinspires.org/robotics/frc/blog/2020-kickoff-downloads)
    kickoff_2020 = datetime(2020, 1, 4, 10, 30, 00, tzinfo=EST)
    kickoff_2020_utc = kickoff_2020.astimezone(UTC)
    assert SeasonHelper.kickoff_datetime_est(year=2020) == kickoff_2020
    assert SeasonHelper.kickoff_datetime_utc(year=2020) == kickoff_2020_utc

    # 2019 - Saturday the 5th, 10:30am EST (https://en.wikipedia.org/wiki/Logo_Motion)
    kickoff_2019 = datetime(2019, 1, 5, 10, 30, 00, tzinfo=EST)
    kickoff_2019_utc = kickoff_2019.astimezone(UTC)
    assert SeasonHelper.kickoff_datetime_est(year=2019) == kickoff_2019
    assert SeasonHelper.kickoff_datetime_utc(year=2019) == kickoff_2019_utc

    # 2010 - Saturday the 9th, 10:30am EST (https://en.wikipedia.org/wiki/Breakaway_(FIRST))
    kickoff_2010 = datetime(2010, 1, 9, 10, 30, 00, tzinfo=EST)
    kickoff_2010_utc = kickoff_2010.astimezone(UTC)
    assert SeasonHelper.kickoff_datetime_est(year=2010) == kickoff_2010
    assert SeasonHelper.kickoff_datetime_utc(year=2010) == kickoff_2010_utc
