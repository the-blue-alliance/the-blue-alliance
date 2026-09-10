import json

import pytest
from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.insight import Insight


def test_insights_single_year_endpoint(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    insight_data = {
        "key_type": "team",
        "rankings": [
            {"keys": ["frc1"], "value": 2},
            {
                "keys": ["frc2", "frc3"],
                "value": 1,
            },
        ],
    }

    Insight(
        name=Insight.INSIGHT_NAMES[Insight.TYPED_LEADERBOARD_BLUE_BANNERS],
        year=2024,
        data_json=json.dumps(insight_data),
    ).put()

    resp = api_client.get(
        "/api/v3/insights/leaderboards/2024",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == [
        {
            "data": insight_data,
            "name": "typed_leaderboard_blue_banners",
            "year": 2024,
        }
    ]

    resp = api_client.get(
        "/api/v3/insights/leaderboards/2023",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == []

    resp = api_client.get(
        "/api/v3/insights/leaderboards/0",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == []


def test_insights_notables_single_year_endpoint(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    insight_data = {
        "entries": [
            {"team_key": "frc1", "context": ["2024mil"]},
            {"team_key": "frc2", "context": ["2024hop"]},
            {"team_key": "frc3", "context": ["2024hop"]},
        ]
    }

    Insight(
        name=Insight.INSIGHT_NAMES[Insight.TYPED_NOTABLES_DIVISION_WINNERS],
        year=2024,
        data_json=json.dumps(insight_data),
    ).put()

    resp = api_client.get(
        "/api/v3/insights/notables/2024",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == [
        {
            "data": insight_data,
            "name": "notables_division_winners",
            "year": 2024,
        }
    ]

    resp = api_client.get(
        "/api/v3/insights/notables/2023",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == []

    resp = api_client.get(
        "/api/v3/insights/notables/0",
        headers={"X-TBA-Auth-Key": "test_auth_key"},
    )
    assert resp.status_code == 200
    assert resp.json == []


def test_insights_models_query_response_passthrough(
    ndb_stub, api_client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    Insight(
        name=Insight.INSIGHT_NAMES[Insight.TYPED_LEADERBOARD_BLUE_BANNERS],
        year=2024,
        data_json=json.dumps({"key_type": "team", "rankings": []}),
    ).put()
    Insight(
        name=Insight.INSIGHT_NAMES[Insight.TYPED_NOTABLES_DIVISION_WINNERS],
        year=2024,
        data_json=json.dumps({"entries": []}),
    ).put()

    headers = {"X-TBA-Auth-Key": "test_auth_key"}

    from backend.common.consts.api_version import ApiMajorVersion
    from backend.common.queries.database_query import CachedDatabaseQuery
    from backend.common.queries.insight_query import (
        InsightsLeaderboardsYearQuery,
        InsightsNotablesYearQuery,
    )

    orig_fetch_json = CachedDatabaseQuery.fetch_json
    orig_fetch_dict = CachedDatabaseQuery.fetch_dict
    calls_fetch_json = []
    calls_fetch_dict = []

    def spy_fetch_json(self, version):
        calls_fetch_json.append((type(self), version))
        return orig_fetch_json(self, version)

    def spy_fetch_dict(self, version):
        calls_fetch_dict.append((type(self), version))
        return orig_fetch_dict(self, version)

    monkeypatch.setattr(CachedDatabaseQuery, "fetch_json", spy_fetch_json)
    monkeypatch.setattr(CachedDatabaseQuery, "fetch_dict", spy_fetch_dict)

    # 1. insights_leaderboards_year (fetch_json)
    calls_fetch_json.clear()
    calls_fetch_dict.clear()
    resp = api_client.get("/api/v3/insights/leaderboards/2024", headers=headers)
    assert resp.status_code == 200
    assert len(calls_fetch_json) == 1
    assert calls_fetch_json[0] == (
        InsightsLeaderboardsYearQuery,
        ApiMajorVersion.API_V3,
    )
    assert len(calls_fetch_dict) == 0

    # 2. insights_notables_year (fetch_json)
    calls_fetch_json.clear()
    calls_fetch_dict.clear()
    resp = api_client.get("/api/v3/insights/notables/2024", headers=headers)
    assert resp.status_code == 200
    assert len(calls_fetch_json) == 1
    assert calls_fetch_json[0] == (InsightsNotablesYearQuery, ApiMajorVersion.API_V3)
    assert len(calls_fetch_dict) == 0
