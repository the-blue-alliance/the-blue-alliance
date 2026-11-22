from backend.api.handlers.tests.api_spec import (
    component_schema_errors,
    response_schema_errors,
    undeclared_fields,
)

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


def test_component_schema_errors_names_mistyped_field() -> None:
    body = {**TEAM_SIMPLE, "team_number": "254"}

    assert component_schema_errors("Team_Simple", body) == [
        "$.team_number: '254' is not of type 'integer'"
    ]


def test_undeclared_fields_empty_for_declared_body() -> None:
    assert undeclared_fields("Team_Simple", TEAM_SIMPLE) == []


def test_undeclared_fields_names_extra_key() -> None:
    body = {**TEAM_SIMPLE, "rookie_year": 1999}

    assert undeclared_fields("Team_Simple", body) == ["$.rookie_year"]
