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
