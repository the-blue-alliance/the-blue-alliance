from unittest.mock import call, patch

import pytest

from backend.common.frc_api import FRCAPI
from backend.common.futures import InstantFuture
from backend.common.models.regional_pool_advancement import (
    ChampionshipStatus,
    TeamRegionalPoolAdvancement,
)
from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
)
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_fms_api import DatafeedFMSAPI
from backend.tasks_io.datafeeds.parsers.fms_api.fms_api_regional_rankings_parser import (
    FMSAPIRegionalRankingsParser,
    TParsedRegionalAdvancement,
)


@pytest.fixture(autouse=True)
def fms_api_secrets(ndb_stub) -> None:
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))


def test_get_regional_rankings() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2025/rankings/regional/teamdetail?page=1",
        200,
        "{}",
    )

    df = DatafeedFMSAPI()
    with (
        patch.object(
            FRCAPI, "regional_rankings", return_value=InstantFuture(response)
        ) as mock_api,
        patch.object(FMSAPIRegionalRankingsParser, "parse") as mock_parse,
    ):
        mock_parse.side_effect = [
            (
                TParsedRegionalAdvancement(
                    advancement={
                        "frc254": TeamRegionalPoolAdvancement(
                            cmp=True, cmp_status=ChampionshipStatus.EVENT_QUALIFIED
                        )
                    },
                    adjustments={"frc254": 5},
                ),
                False,
            )
        ]
        result = df.get_regional_rankings(2025).get_result()

    mock_api.assert_called_once_with(2025, 1)
    mock_parse.assert_called_once_with(response.json())
    assert result == TParsedRegionalAdvancement(
        advancement={
            "frc254": TeamRegionalPoolAdvancement(
                cmp=True, cmp_status=ChampionshipStatus.EVENT_QUALIFIED
            )
        },
        adjustments={"frc254": 5},
    )


def test_get_regional_rankings_paginated() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2025/rankings/regional/teamdetail?page=1",
        200,
        "{}",
    )

    df = DatafeedFMSAPI()
    with (
        patch.object(
            FRCAPI, "regional_rankings", return_value=InstantFuture(response)
        ) as mock_api,
        patch.object(FMSAPIRegionalRankingsParser, "parse") as mock_parse,
    ):
        mock_parse.side_effect = [
            (
                TParsedRegionalAdvancement(
                    advancement={
                        "frc254": TeamRegionalPoolAdvancement(
                            cmp=True, cmp_status=ChampionshipStatus.EVENT_QUALIFIED
                        )
                    },
                    adjustments={},
                ),
                True,
            ),
            (
                TParsedRegionalAdvancement(
                    advancement={
                        "frc1678": TeamRegionalPoolAdvancement(
                            cmp=True, cmp_status=ChampionshipStatus.POOL_QUALIFIED
                        )
                    },
                    adjustments={"frc1678": -2},
                ),
                False,
            ),
        ]
        result = df.get_regional_rankings(2025).get_result()

    mock_api.assert_has_calls([call(2025, 1), call(2025, 2)])
    mock_parse.assert_has_calls([call(response.json()), call(response.json())])
    # Pages are merged together
    assert set(result.advancement.keys()) == {"frc254", "frc1678"}
    assert result.adjustments == {"frc1678": -2}


def test_get_regional_rankings_fetch_failed() -> None:
    response = URLFetchResult.mock_for_content(
        "https://frc-api.firstinspires.org/v3.0/2025/rankings/regional/teamdetail?page=1",
        500,
        "",
    )

    df = DatafeedFMSAPI()
    with (
        patch.object(
            FRCAPI, "regional_rankings", return_value=InstantFuture(response)
        ) as mock_api,
        patch.object(FMSAPIRegionalRankingsParser, "parse") as mock_parse,
    ):
        result = df.get_regional_rankings(2025).get_result()

    mock_api.assert_called_once_with(2025, 1)
    mock_parse.assert_not_called()
    assert result == TParsedRegionalAdvancement(advancement={}, adjustments={})
