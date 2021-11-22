import logging
from unittest.mock import Mock, patch

import pytest

from backend.common.sitevars.fms_api_secrets import ContentType as FMSApiSecretsContentType
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.tasks_io.datafeeds.datafeed_fms_api_v3 import DatafeedFMSAPIV3


# Note to Zach: These tests *for sure* need to stub and hit local endpoints
# We can do this with requests, but we need to like, do it.


@pytest.fixture
def fms_api_secrets():
    # TODO: DO NOT PUSH THIS
    FMSApiSecrets.put(FMSApiSecretsContentType(username="", authkey=""))


def test_init_no_fmsapi_secrets():
    with pytest.raises(Exception, match="Missing FMS API auth token. Setup fmsapi.secrets sitevar."):
        df = DatafeedFMSAPIV3()


def test_init_no_fmsapi_secrets_simtime():
    df = DatafeedFMSAPIV3(sim_time="")


def test_init(fms_api_secrets):
    df = DatafeedFMSAPIV3()
    # print(df.get_season(2020))
    print(df.get_index())
    assert False
