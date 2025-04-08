import datetime

from backend.common.sitevars.apistatus import (
    AndroidConfig,
    ApiStatus,
    ContentType,
    IOSConfig,
    WebConfig,
)


def test_key():
    assert ApiStatus.key() == "apistatus"


def test_description():
    assert ApiStatus.description() == "For setting max year, min app versions, etc."


def test_default_sitevar():
    default_sitevar = ApiStatus._fetch_sitevar()
    assert default_sitevar is not None

    year = datetime.datetime.now().year
    default_json = {
        "android": None,
        "current_season": year,
        "ios": None,
        "max_season": year,
        "web": None,
        "max_team_page": 0,
    }
    assert default_sitevar.contents == default_json
    assert default_sitevar.description == "For setting max year, min app versions, etc."


def test_status_empty():
    year = datetime.datetime.now().year
    assert ApiStatus.status() == {
        "android": None,
        "current_season": year,
        "ios": None,
        "max_season": year,
        "web": None,
        "max_team_page": 0,
    }


def test_status_full():
    year = datetime.datetime.now().year
    values_json = {
        "android": {"min_app_version": 1, "latest_app_version": 2},
        "current_season": year,
        "ios": {
            "min_app_version": 3,
            "latest_app_version": 4,
        },
        "max_season": year,
        "web": {
            "travis_job": "abc",
            "tbaClient_endpoints_sha": "abc",
            "current_commit": "abc",
            "deploy_time": "abc",
            "endpoints_sha": "abc",
            "commit_time": "abc",
        },
        "max_team_page": 0,
    }
    ApiStatus.put(
        ContentType(
            current_season=year,
            max_season=year,
            web=WebConfig(
                travis_job="abc",
                tbaClient_endpoints_sha="abc",
                current_commit="abc",
                deploy_time="abc",
                endpoints_sha="abc",
                commit_time="abc",
            ),
            android=AndroidConfig(min_app_version=1, latest_app_version=2),
            ios=IOSConfig(min_app_version=3, latest_app_version=4),
            max_team_page=0,
        )
    )
    assert ApiStatus.status() == values_json
