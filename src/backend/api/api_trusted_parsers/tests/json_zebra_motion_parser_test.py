import copy
import json
from typing import Any, Dict, List

import pytest

from backend.api.api_trusted_parsers.json_zebra_motionworks_parser import (
    JSONZebraMotionWorksParser,
)
from backend.common.datafeed_parsers.exceptions import ParserInputException


@pytest.fixture
def zebra_data() -> List[Dict[str, Any]]:
    return [
        {
            "key": "2020casj_qm1",
            "times": [0.0, 0.5, 1.0, 1.5],
            "alliances": {
                "red": [
                    {
                        "team_key": "frc254",
                        "xs": [None, 1.2, 1.3, 1.4],
                        "ys": [None, 0.1, 0.1, 0.1],
                    },
                    {
                        "team_key": "frc971",
                        "xs": [1.1, 1.2, 1.3, 1.4],
                        "ys": [0.1, 0.1, 0.1, 0.1],
                    },
                    {
                        "team_key": "frc604",
                        "xs": [1.1, 1.2, 1.3, 1.4],
                        "ys": [0.1, 0.1, 0.1, 0.1],
                    },
                ],
                "blue": [
                    {
                        "team_key": "frc1",
                        "xs": [None, 1.2, 1.3, 1.4],
                        "ys": [None, 0.1, 0.1, 0.1],
                    },
                    {
                        "team_key": "frc2",
                        "xs": [1.1, 1.2, 1.3, 1.4],
                        "ys": [0.1, 0.1, 0.1, 0.1],
                    },
                    {
                        "team_key": "frc3",
                        "xs": [1.1, 1.2, None, 1.4],
                        "ys": [0.1, 0.1, None, 0.1],
                    },
                ],
            },
        }
    ]


def test_parser(zebra_data: List[Dict[str, Any]]) -> None:
    parsed = JSONZebraMotionWorksParser.parse(json.dumps(zebra_data))
    assert parsed == zebra_data


def test_not_list_of_dicts() -> None:
    with pytest.raises(ParserInputException):
        JSONZebraMotionWorksParser.parse("""["some", "bad", "input"]""")


def test_missing_times(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    del data[0]["times"]
    with pytest.raises(ParserInputException):
        JSONZebraMotionWorksParser.parse(json.dumps(data))


def test_empty_times(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    data[0]["times"] = []
    with pytest.raises(ParserInputException):
        JSONZebraMotionWorksParser.parse(json.dumps(data))


def test_null_times(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    data[0]["times"][0] = None
    with pytest.raises(ParserInputException):
        JSONZebraMotionWorksParser.parse(json.dumps(data))


def test_int_times(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    data[0]["times"][0] = 0
    with pytest.raises(ParserInputException):
        JSONZebraMotionWorksParser.parse(json.dumps(data))


def test_missing_team_key(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    del data[0]["alliances"]["red"][0]["team_key"]
    with pytest.raises(ParserInputException):
        JSONZebraMotionWorksParser.parse(json.dumps(data))


def test_malformatted_team_key(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    data[0]["alliances"]["red"][0]["team_key"] = "254"
    with pytest.raises(ParserInputException):
        JSONZebraMotionWorksParser.parse(json.dumps(data))


def test_missing_coords(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    del data[0]["alliances"]["red"][0]["xs"]
    with pytest.raises(ParserInputException):
        JSONZebraMotionWorksParser.parse(json.dumps(data))


def test_int_coords(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    data[0]["alliances"]["red"][0]["xs"][0] = 0
    with pytest.raises(ParserInputException):
        JSONZebraMotionWorksParser.parse(json.dumps(data))


def test_mismatched_null_coords(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    data[0]["alliances"]["red"][0]["xs"][1] = None
    with pytest.raises(ParserInputException):
        JSONZebraMotionWorksParser.parse(json.dumps(data))


def test_invalid_json() -> None:
    with pytest.raises(ParserInputException):
        JSONZebraMotionWorksParser.parse("not json at all")


def test_times_not_a_list(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    data[0]["times"] = {"0": 0.0}
    with pytest.raises(ParserInputException, match="array of 'times'"):
        JSONZebraMotionWorksParser.parse(json.dumps(data))


def test_missing_alliances(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    del data[0]["alliances"]
    with pytest.raises(ParserInputException, match="dictionary of 'alliances'"):
        JSONZebraMotionWorksParser.parse(json.dumps(data))


def test_alliances_not_a_dict(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    data[0]["alliances"] = [data[0]["alliances"]["red"]]
    with pytest.raises(ParserInputException, match="dictionary of 'alliances'"):
        JSONZebraMotionWorksParser.parse(json.dumps(data))


def test_alliance_wrong_team_count(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    del data[0]["alliances"]["blue"][2]
    with pytest.raises(ParserInputException, match="Must have 3 teams per alliance"):
        JSONZebraMotionWorksParser.parse(json.dumps(data))


def test_missing_alliance(zebra_data: List[Dict[str, Any]]) -> None:
    data = copy.deepcopy(zebra_data)
    del data[0]["alliances"]["red"]
    with pytest.raises(ParserInputException, match="Must have 3 teams per alliance"):
        JSONZebraMotionWorksParser.parse(json.dumps(data))
