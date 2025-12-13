import json

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
