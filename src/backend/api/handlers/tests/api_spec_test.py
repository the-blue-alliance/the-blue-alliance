from backend.api.handlers.tests.api_spec import response_schema_errors

TEAM_SIMPLE = {
    "key": "frc254",
    "team_number": 254,
    "nickname": "The Cheesy Poofs",
    "name": "NASA Ames Research Center",
    "city": "San Jose",
    "state_prov": "CA",
    "country": "USA",
}


def test_response_schema_errors_empty_for_valid_body() -> None:
    assert response_schema_errors("/team/{team_key}/simple", TEAM_SIMPLE) == []


def test_response_schema_errors_names_mistyped_field() -> None:
    body = {**TEAM_SIMPLE, "team_number": "254"}

    assert response_schema_errors("/team/{team_key}/simple", body) == [
        "$.team_number: '254' is not of type 'integer'"
    ]
