import datetime
import json
import os
from typing import Any
from unittest import mock
from unittest.mock import patch

import pytest
from google.appengine.api import urlfetch_errors
from google.appengine.ext import testbed

from backend.common.frc_api import FRCAPI
from backend.common.sitevars.fms_api_secrets import (
    ContentType as FMSApiSecretsContentType,
)
from backend.common.sitevars.fms_api_secrets import FMSApiSecrets
from backend.common.storage import (
    get_files as cloud_storage_get_files,
    read as cloud_storage_read,
)


@pytest.fixture(autouse=True)
def auto_add_urlfetch_stub(
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    pass


@pytest.fixture(autouse=True)
def auto_use_gcs_stub(gcs_stub):
    pass


def test_init_no_fmsapi_secrets(ndb_stub) -> None:
    with pytest.raises(
        Exception, match="Missing FRC API auth token. Setup fmsapi.secrets sitevar."
    ):
        FRCAPI()


def test_init_fmsapi_secrets(ndb_stub) -> None:
    FMSApiSecrets.put(FMSApiSecretsContentType(username="zach", authkey="authkey"))
    api = FRCAPI()
    assert api.auth_token == "emFjaDphdXRoa2V5"


def test_init_auth_token() -> None:
    api = FRCAPI("test")
    assert api.auth_token == "test"


def test_init_with_credentials() -> None:
    api = FRCAPI.with_credentials("zach", "authkey")
    assert api.auth_token == "emFjaDphdXRoa2V5"


def test_root() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.root()

    mock_get.assert_called_once_with("/", mock.ANY)


def test_event_list_pre_2026() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_list(2020)
    mock_get.assert_called_once_with("/2020/events", mock.ANY, version="v3.0")


def test_event_list_post_2026() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_list(2026)
    mock_get.assert_called_once_with("/2026/events", mock.ANY, version="v3.3")


def test_event_info_pre_2026() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_info(2020, "MIKET")
    mock_get.assert_called_once_with(
        "/2020/events?eventCode=MIKET", mock.ANY, version="v3.0"
    )


def test_event_info_post_2026() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_info(2026, "MIKET")
    mock_get.assert_called_once_with(
        "/2026/events?eventCode=MIKET", mock.ANY, version="v3.3"
    )


def test_event_teams() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_teams(2020, "MIKET", 1)
    mock_get.assert_called_once_with("/2020/teams?eventCode=MIKET&page=1", mock.ANY)


def test_event_team_avatars() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.event_team_avatars(2020, "MIKET", 1)
    mock_get.assert_called_once_with("/2020/avatars?eventCode=MIKET&page=1", mock.ANY)


def test_event_alliances() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.alliances(2020, "MIKET")
    mock_get.assert_called_once_with("/2020/alliances/MIKET", mock.ANY)


def test_event_rankings() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.rankings(2020, "MIKET")
    mock_get.assert_called_once_with("/2020/rankings/MIKET", mock.ANY)


def test_event_schedule() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.match_schedule(2020, "MIKET", "qual")
    mock_get.assert_called_once_with(
        "/2020/schedule/MIKET?tournamentLevel=qual", mock.ANY
    )


def test_event_matches() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.matches(2020, "MIKET", "qual")
    mock_get.assert_called_once_with(
        "/2020/matches/MIKET?tournamentLevel=qual", mock.ANY
    )


def test_event_scores() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.match_scores(2020, "MIKET", "qual")
    mock_get.assert_called_once_with("/2020/scores/MIKET/qual", mock.ANY)


def test_awards_no_event_code_no_team_number() -> None:
    api = FRCAPI("zach")
    with pytest.raises(
        FRCAPI.ValidationError,
        match="awards expects either an event_code, team_number, or both",
    ):
        api.awards(2020)


def test_awards_event_code() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.awards(2020, event_code="MIKET")

    mock_get.assert_called_once_with("/2020/awards/event/MIKET", mock.ANY)


def test_awards_team_number() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.awards(2020, team_number=2337)

    mock_get.assert_called_once_with("/2020/awards/team/2337", mock.ANY)


def test_awards_event_code_team_number() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.awards(2020, event_code="MIKET", team_number=2337)

    mock_get.assert_called_once_with("/2020/awards/eventteam/MIKET/2337", mock.ANY)


def test_district_list() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.district_list(2020)
    mock_get.assert_called_once_with("/2020/districts", mock.ANY)


def test_district_rankings() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.district_rankings(2020, "ne", 1)
    mock_get.assert_called_once_with(
        "/2020/rankings/district?districtCode=ne&page=1", mock.ANY
    )


def test_team_details() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.team_details(2020, 254)
    mock_get.assert_called_once_with("/2020/teams?teamNumber=254", mock.ANY)


def test_team_avatars() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.team_avatar(2020, 254)
    mock_get.assert_called_once_with("/2020/avatars?teamNumber=254", mock.ANY)


@pytest.mark.parametrize(
    "endpoint", ["/2020/awards/MIKET", "2020/awards/MIKET", "///2020/awards/MIKET"]
)
def test_get(
    endpoint: str, urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub
) -> None:
    api = FRCAPI("zach")

    expected_url = "https://frc-api.firstinspires.org/v3.0/2020/awards/MIKET"
    expected_headers = {
        "Accept": "application/json",
        "Authorization": "Basic zach",
        "Cache-Control": "no-cache, max-age=10",
        "Pragma": "no-cache",
    }

    with patch.object(urlfetch_stub, "_Dynamic_Fetch") as mock_fetch:
        api._get(endpoint, Any).get_result()

    assert mock_fetch.call_count == 1
    called_request = mock_fetch.call_args[0][0]
    assert called_request.Url == expected_url

    called_headers = {h.Key: h.Value for h in called_request.header}
    assert called_headers == expected_headers


def test_get_deadline_exceeded_returns_408(
    monkeypatch: pytest.MonkeyPatch,
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")

    api = FRCAPI("zach", save_response=True)

    with patch.object(
        urlfetch_stub,
        "_Dynamic_Fetch",
        side_effect=urlfetch_errors.DeadlineExceededError("deadline exceeded"),
    ):
        response = api.root().get_result()

    assert response.status_code == 408
    assert response.content == b""
    assert cloud_storage_get_files("frc-api-response/v3.0/") == []


def _mock_frc_api(
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
    content: dict,
    overwrite_idx: int | None = None,
) -> int:

    def is_frc_api(url: str) -> bool:
        if "frc-api.firstinspires.org" in url:
            return True
        return False

    def mock_fetch_fn(
        url,
        payload,
        method,
        headers,
        request,
        response,
        follow_redirects,
        deadline,
        validate_certificate,
    ):
        response.StatusCode = 200
        response.Content = json.dumps(content).encode()

    if overwrite_idx is not None:
        urlfetch_stub._urlmatchers_to_fetch_functions[overwrite_idx] = (
            is_frc_api,
            mock_fetch_fn,
        )
        return overwrite_idx
    else:
        urlfetch_stub._urlmatchers_to_fetch_functions.append(
            (is_frc_api, mock_fetch_fn)
        )
        return len(urlfetch_stub._urlmatchers_to_fetch_functions) - 1


def test_save_response(
    monkeypatch: pytest.MonkeyPatch,
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")
    content = {
        "currentSeason": 2021,
        "maxSeason": 2021,
        "name": "FIRST ROBOTICS COMPETITION API",
        "apiVersion": "3.0",
        "status": "normal",
    }

    _mock_frc_api(urlfetch_stub, content)

    api = FRCAPI("zach", save_response=True)
    api.root().get_result()

    files = cloud_storage_get_files("frc-api-response/v3.0/")
    assert len(files) == 1

    f = cloud_storage_read(files[0])
    assert f is not None
    assert f == json.dumps(content).encode()


def test_save_response_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")
    content = {
        "currentSeason": 2021,
        "maxSeason": 2021,
        "name": "FIRST ROBOTICS COMPETITION API",
        "apiVersion": "3.0",
        "status": "normal",
    }

    _mock_frc_api(urlfetch_stub, content)
    api = FRCAPI("zach", save_response=True)
    api.root().get_result()

    files = cloud_storage_get_files("frc-api-response/v3.0/")
    assert len(files) == 1
    f_name = files[0]

    # Since the content didn't change, we shouldn't have written another
    api.root().get_result()
    assert cloud_storage_get_files("frc-api-response/v3.0/") == [f_name]


def test_save_response_updated(
    monkeypatch: pytest.MonkeyPatch,
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")
    content = {
        "currentSeason": 2021,
        "maxSeason": 2021,
        "name": "FIRST ROBOTICS COMPETITION API",
        "apiVersion": "3.0",
        "status": "normal",
    }

    idx = _mock_frc_api(urlfetch_stub, content)
    api = FRCAPI("zach", save_response=True)
    api.root().get_result()

    files = cloud_storage_get_files("frc-api-response/v3.0/")
    assert len(files) == 1

    content2 = {
        "currentSeason": 2021,
        "maxSeason": 2021,
        "name": "SECOND ROBOTICS COMPETITION API",
        "apiVersion": "3.0",
        "status": "normal",
    }

    _mock_frc_api(urlfetch_stub, content2, overwrite_idx=idx)
    api.root().get_result()

    # Since the content is different, we should have two items
    files = cloud_storage_get_files("frc-api-response/v3.0/")
    assert len(files) == 2

    f = cloud_storage_read(files[0])
    assert f is not None
    assert f == json.dumps(content).encode()

    f2 = cloud_storage_read(files[1])
    assert f2 is not None
    assert f2 == json.dumps(content2).encode()


def test_response_content_and_saved_snapshot_are_bytes(
    monkeypatch: pytest.MonkeyPatch,
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    # Pins the runtime types behind the `content: bytes` and `read -> bytes` annotations.
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")
    _mock_frc_api(urlfetch_stub, {"currentSeason": 2021})
    response = FRCAPI("zach", save_response=True).root().get_result()

    files = cloud_storage_get_files("frc-api-response/v3.0/")
    assert len(files) == 1
    assert isinstance(response.content, bytes)
    assert isinstance(cloud_storage_read(files[0]), bytes)


def test_regional_rankings() -> None:
    api = FRCAPI("zach")
    with patch.object(FRCAPI, "_get") as mock_get:
        api.regional_rankings(2025, 2)
    mock_get.assert_called_once_with(
        "/2025/rankings/regional/teamdetail?page=2", mock.ANY
    )


def test_save_response_disabled(
    monkeypatch: pytest.MonkeyPatch,
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")
    _mock_frc_api(urlfetch_stub, {"status": "normal"})

    api = FRCAPI("zach", save_response=False)
    api.root().get_result()

    assert cloud_storage_get_files("frc-api-response/v3.0/") == []


def test_save_response_storage_error(
    monkeypatch: pytest.MonkeyPatch,
    urlfetch_stub: testbed.urlfetch_stub.URLFetchServiceStub,
) -> None:
    monkeypatch.setenv("SAVE_FRC_API_RESPONSE", "true")
    _mock_frc_api(urlfetch_stub, {"status": "normal"})

    api = FRCAPI("zach", save_response=True)
    with patch("backend.common.storage.get_files", side_effect=Exception("gcs down")):
        # Storage errors are logged, not raised
        resp = api.root().get_result()

    assert resp.status_code == 200


def test_get_cached_gcs_files_downloads_and_caches(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from backend.common.frc_api import frc_api as frc_api_module

    monkeypatch.setattr(frc_api_module, "__file__", str(tmp_path / "frc_api.py"))
    gcs_dir = "frc-api-response/v3.0/2020/root/"
    contents = {
        f"{gcs_dir}2020-03-01 10:00:00.0.json": b"first",
        f"{gcs_dir}2020-03-02 10:00:00.0.json": b"second",
        f"{gcs_dir}2020-03-03 10:00:00.0.json": None,
    }
    with (
        patch("backend.common.storage.get_files", return_value=list(contents)),
        patch("backend.common.storage.read", side_effect=contents.get),
    ):
        files = FRCAPI.get_cached_gcs_files(gcs_dir)

    safe_dir = "frc-api-response/v3.0/2020/root/"
    # Only the file names are asserted here; the returned path shape is
    # covered by a separate test.
    assert [os.path.basename(f) for f in files] == [
        "2020-03-01 10_00_00.0.json",
        "2020-03-02 10_00_00.0.json",
    ]
    cache_dir = tmp_path / "gcs_test_data_cache" / safe_dir
    assert (cache_dir / "2020-03-01 10_00_00.0.json").read_bytes() == b"first"
    assert (cache_dir / "2020-03-02 10_00_00.0.json").read_bytes() == b"second"
    assert not (cache_dir / "2020-03-03 10_00_00.0.json").exists()

    # A second lookup is served from the local cache
    with patch("backend.common.storage.get_files") as mock_get_files:
        cached = FRCAPI.get_cached_gcs_files(gcs_dir)
    mock_get_files.assert_not_called()
    assert sorted(cached) == sorted(
        [
            f"{safe_dir}2020-03-01 10_00_00.0.json",
            f"{safe_dir}2020-03-02 10_00_00.0.json",
        ]
    )


def test_get_cached_gcs_files_same_paths_downloaded_or_cached(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Downloaded and cached GCS files have the same dir/file paths."""
    from backend.common.frc_api import frc_api as frc_api_module

    monkeypatch.setattr(frc_api_module, "__file__", str(tmp_path / "frc_api.py"))
    gcs_dir = "frc-api-response/v3.0/2020/root/"
    contents = {f"{gcs_dir}2020-03-01 10:00:00.0.json": b"text"}
    with (
        patch("backend.common.storage.get_files", return_value=list(contents)),
        patch("backend.common.storage.read", side_effect=contents.get),
    ):
        downloaded = FRCAPI.get_cached_gcs_files(gcs_dir)
    cached = FRCAPI.get_cached_gcs_files(gcs_dir)

    expected = [f"{gcs_dir}2020-03-01 10_00_00.0.json"]
    assert downloaded == expected
    assert cached == expected


def test_simulated_v2_schedule_uses_hybrid_endpoint() -> None:
    api = FRCAPI("zach", sim_time=datetime.datetime(2022, 3, 1), sim_api_version="v2.0")
    with patch.object(FRCAPI, "_get_api_response_from_gcs") as mock_gcs:
        api._get_simulated("/2022/schedule/CADA?tournamentLevel=qual", dict, "v2.0")
    mock_gcs.assert_called_once_with("/2022/schedule/CADA/qual/hybrid", "v2.0", dict)


def test_simulated_response_no_files() -> None:
    api = FRCAPI("zach", sim_time=datetime.datetime(2022, 3, 1))
    with patch.object(FRCAPI, "get_cached_gcs_files", return_value=[]):
        resp = api._get_api_response_from_gcs("/2022/teams", "v3.0", dict)
    assert resp.status_code == 200
    assert resp.json() == {}


def test_simulated_response_error() -> None:
    api = FRCAPI("zach", sim_time=datetime.datetime(2022, 3, 1))
    with patch.object(
        FRCAPI, "get_cached_gcs_files", return_value=["dir/not-a-timestamp.json"]
    ):
        resp = api._get_api_response_from_gcs("/2022/teams", "v3.0", dict)
    assert resp.status_code == 500


def test_merge_schedule_without_results() -> None:
    api = FRCAPI("zach")
    schedule = {"Schedule": [{"matchNumber": 1, "teams": []}]}
    assert api._merge_match_schedule_and_results(schedule, {}) == {
        "Schedule": [{"matchNumber": 1, "teams": []}]
    }


def test_merge_match_normalizes_capitalized_teams() -> None:
    """A "Teams" key on both sides is merged and normalized to "teams"."""
    scheduled = {"Teams": [{"teamNumber": 254, "station": "Red1"}]}
    merged = FRCAPI._merge_match(
        scheduled, {"Teams": [{"teamNumber": 254, "dq": False}]}
    )
    assert merged["teams"] == [{"teamNumber": 254, "station": "Red1", "dq": False}]
    assert "Teams" not in merged


@pytest.mark.parametrize(
    "schedule_key, result_key",
    [("teams", "Teams"), ("Teams", "teams")],
)
def test_merge_match_merges_mixed_case_teams(
    schedule_key: str, result_key: str
) -> None:
    """Result team flags reach the scheduled teams whatever the key capitalisation."""
    scheduled = {schedule_key: [{"teamNumber": 254, "station": "Red1"}]}
    merged = FRCAPI._merge_match(
        scheduled, {result_key: [{"teamNumber": 254, "surrogate": True}]}
    )
    assert merged["teams"] == [
        {"teamNumber": 254, "station": "Red1", "surrogate": True}
    ]
    assert "Teams" not in merged


def test_merge_match_clears_capitalized_placeholder_teams() -> None:
    """The {1, 2, 3} placeholder teams are cleared when the schedule uses "Teams"."""
    scheduled = {
        "Teams": [
            {"teamNumber": 1, "station": "Red1"},
            {"teamNumber": 2, "station": "Red2"},
            {"teamNumber": 3, "station": "Red3"},
        ]
    }
    merged = FRCAPI._merge_match(scheduled, {"scoreRedFinal": 10})
    assert merged["teams"] == [
        {"teamNumber": None, "station": "Red1"},
        {"teamNumber": None, "station": "Red2"},
        {"teamNumber": None, "station": "Red3"},
    ]
    assert "Teams" not in merged


def test_merge_match_schedule_without_teams() -> None:
    merged = FRCAPI._merge_match(
        {"matchNumber": 1}, {"teams": [{"teamNumber": 254, "dq": False}]}
    )
    assert merged["teams"] == [{"teamNumber": 254, "dq": False}]


def test_merge_match_placeholder_teams() -> None:
    scheduled = {
        "teams": [
            {"teamNumber": 1, "station": "Red1"},
            {"teamNumber": 2, "station": "Red2"},
            {"teamNumber": 3, "station": "Red3"},
        ]
    }
    merged = FRCAPI._merge_match(scheduled, {"scoreRedFinal": 10})
    assert merged["teams"] == [
        {"teamNumber": None, "station": "Red1"},
        {"teamNumber": None, "station": "Red2"},
        {"teamNumber": None, "station": "Red3"},
    ]
    assert merged["scoreRedFinal"] == 10
