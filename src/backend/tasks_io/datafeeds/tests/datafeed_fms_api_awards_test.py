from unittest.mock import call, patch

import pytest
from google.appengine.ext import ndb

from backend.common.consts.event_type import EventType
from backend.common.frc_api import FRCAPI
from backend.common.futures import InstantFuture
from backend.common.models.event import Event
from backend.common.models.event_team import EventTeam
from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
)
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_awards_parser import (
    FMSAPIAwardsParser,
)


@pytest.fixture(autouse=True)
def fms_api_secrets(ndb_stub):
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))


@pytest.mark.parametrize("first_code, event_short", [("miket", None), (None, "miket")])
def test_get_awards_event(first_code, event_short):
    event = Event(
        event_type_enum=EventType.DISTRICT,
        first_code=first_code,
        event_short=event_short,
        year=2020,
    )

    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2020/awards/MIKET/0",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "awards", return_value=InstantFuture(response)
    ) as mock_awards, patch.object(
        FMSAPIAwardsParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPIAwardsParser, "parse"
    ) as mock_parse:
        df.get_awards(event).get_result()

    mock_awards.assert_called_once_with(2020, event_code="miket")
    mock_init.assert_called_once_with(event)
    mock_parse.assert_called_once_with(response.json())


@pytest.mark.parametrize("first_code, event_short", [("galileo", None), (None, "gal")])
def test_get_awards_event_cmp(first_code, event_short):
    event = Event(
        event_type_enum=EventType.CMP_DIVISION,
        first_code=first_code,
        event_short=event_short,
        year=2014,
    )

    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2014/awards/GALILEO/0",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "awards", return_value=InstantFuture(response)
    ) as mock_awards, patch.object(
        FMSAPIAwardsParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPIAwardsParser, "parse"
    ) as mock_parse:
        df.get_awards(event).get_result()

    mock_awards.assert_called_once_with(2014, event_code="galileo")
    mock_init.assert_called_once_with(event)
    mock_parse.assert_called_once_with(response.json())


@pytest.mark.parametrize("teams", [[], [7332]])
def test_get_awards_event_cmp_2015(teams):
    event = Event(
        id="2015gal",
        event_short="gal",
        year=2015,
        event_type_enum=EventType.CMP_DIVISION,
    )
    event.put()

    for team in teams:
        # Insert EventTeams
        EventTeam(
            id=f"{event.key_name}_frc{team}",
            event=event.key,
            team=ndb.Key("Team", f"frc{team}"),
            year=2015,
        ).put()

    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2014/awards/GALILEO/7332",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "awards", return_value=InstantFuture(response)
    ) as mock_awards, patch.object(
        FMSAPIAwardsParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPIAwardsParser, "parse"
    ) as mock_parse:
        df.get_awards(event).get_result()

    mock_awards.assert_has_calls(
        [call(2015, event_code="gaca"), call(2015, event_code="galileo")]
    )
    mock_init.assert_has_calls([call(event, set(teams)), call(event)])
    assert mock_parse.call_count == 2


@pytest.mark.parametrize("teams", [[], [7332]])
def test_get_awards_event_cmp_2017(teams):
    event = Event(
        id="2017gal",
        event_short="gal",
        year=2017,
        event_type_enum=EventType.CMP_DIVISION,
    )
    event.put()

    for team in teams:
        # Insert EventTeams
        EventTeam(
            id=f"{event.key_name}_frc{team}",
            event=event.key,
            team=ndb.Key("Team", f"frc{team}"),
            year=2017,
        ).put()

    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2014/awards/GALILEO/7332",
        200,
        "",
    )

    df = DatafeedFMSAPI()
    with patch.object(
        FRCAPI, "awards", return_value=InstantFuture(response)
    ) as mock_awards, patch.object(
        FMSAPIAwardsParser, "__init__", return_value=None
    ) as mock_init, patch.object(
        FMSAPIAwardsParser, "parse"
    ) as mock_parse:
        df.get_awards(event).get_result()

    mock_awards.assert_has_calls(
        [call(2017, event_code="garo"), call(2017, event_code="galileo")]
    )
    mock_init.assert_has_calls([call(event, set(teams)), call(event)])
    assert mock_parse.call_count == 2
