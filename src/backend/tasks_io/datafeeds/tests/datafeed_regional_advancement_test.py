import json
from unittest import mock

import pytest

from backend.common.futures import InstantFuture
from backend.common.sitevars.regional_advancement_api_secrets import (
    ContentType as RegionalAdvancementAPISecretsContentType,
    RegionalAdvancementApiSecret,
)
from backend.common.urlfetch import URLFetchResult
from backend.tasks_io.datafeeds.datafeed_regional_advancement import (
    DatafeedRegionalAdvancement,
)
from backend.tasks_io.datafeeds.parsers.ra.regional_advancement_parser import (
    RegionalAdvancementParser,
    TParsedRegionalAdvancement,
)
from backend.tasks_io.datafeeds.regional_advancement_api import RegionalAdvancementApi


@pytest.fixture()
def ra_api_secrets(ndb_stub) -> None:
    RegionalAdvancementApiSecret.put(
        RegionalAdvancementAPISecretsContentType(url_format="/{year}")
    )


def test_init_requires_secret(ndb_stub) -> None:
    with pytest.raises(Exception):
        DatafeedRegionalAdvancement(2025)


def test_init_bad_year(ndb_stub) -> None:
    with pytest.raises(Exception):
        DatafeedRegionalAdvancement(2019)


@mock.patch.object(RegionalAdvancementParser, "parse")
@mock.patch.object(RegionalAdvancementApi, "cmp_advancement")
def test_get_adancement(
    api_mock: mock.Mock, parser_mock: mock.Mock, ndb_stub, ra_api_secrets
) -> None:
    api_content = TParsedRegionalAdvancement(
        advancement={},
        adjustments={},
    )

    api_response = URLFetchResult.mock_for_content("", 200, json.dumps({}))

    api_mock.return_value = InstantFuture(api_response)
    parser_mock.return_value = api_content

    response = DatafeedRegionalAdvancement(2025).cmp_advancement()
    assert response.get_result() == api_content
