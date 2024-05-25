from backend.api.handlers.helpers.model_properties import (
    simple_event_properties,
    simple_match_properties,
    simple_team_properties,
)
from backend.common.queries.dict_converters.event_converter import EventDict
from backend.common.queries.dict_converters.match_converter import MatchDict
from backend.common.queries.dict_converters.team_converter import TeamDict


def validate_nominal_event_keys(event: EventDict) -> None:
    assert set(event.keys()).difference(set(simple_event_properties)) != set()


def validate_simple_event_keys(event: EventDict) -> None:
    assert set(event.keys()).difference(set(simple_event_properties)) == set()


def validate_nominal_match_keys(match: MatchDict) -> None:
    assert set(match.keys()).difference(set(simple_match_properties)) != set()


def validate_simple_match_keys(match: MatchDict) -> None:
    assert set(match.keys()).difference(set(simple_match_properties)) == set()


def validate_nominal_team_keys(team: TeamDict) -> None:
    assert set(team.keys()).difference(set(simple_team_properties)) != set()


def validate_simple_team_keys(team: TeamDict) -> None:
    assert set(team.keys()).difference(set(simple_team_properties)) == set()
