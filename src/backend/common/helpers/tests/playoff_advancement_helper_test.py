import json
import os
from typing import List, Optional

import pytest

from backend.common.consts.event_type import EventType
from backend.common.consts.playoff_type import PlayoffType
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.playoff_advancement_helper import (
    PlayoffAdvancementHelper,
)
from backend.common.models.alliance import EventAlliance, EventAllianceBackup
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, TeamKey


@pytest.fixture(autouse=True)
def auto_add_ndb_context(ndb_context) -> None:
    pass


def create_event(event_key: EventKey, playoff_type: PlayoffType) -> Event:
    return Event(
        id=event_key,
        event_type_enum=EventType.OFFSEASON,
        year=int(event_key[:4]),
        official=True,
        playoff_type=playoff_type,
    )


@pytest.mark.parametrize(
    "selections,team_keys,output",
    [
        # No alliance selections
        (None, ["frc254", "frc255", "frc256"], None),
        # Alliance not found in list
        ([], ["frc254", "frc255", "frc256"], None),
        # Exact match with explicit name
        (
            [
                EventAlliance(
                    picks=["frc254", "frc255", "frc256"], name="The Couch Alliance"
                )
            ],
            ["frc254", "frc255", "frc256"],
            "The Couch Alliance",
        ),
        # Exact match with implicit name
        (
            [EventAlliance(picks=["frc254", "frc255", "frc256"])],
            ["frc254", "frc255", "frc256"],
            "Alliance 1",
        ),
        # Exact match with backup
        (
            [
                EventAlliance(
                    picks=["frc254", "frc255", "frc256"],
                    backup=EventAllianceBackup(**{"in": "frc257", "out": "frc256"}),
                )
            ],
            ["frc254", "frc255", "frc257"],
            "Alliance 1",
        ),
        # Alliance not found
        (
            [EventAlliance(picks=["frc254", "frc255", "frc256"])],
            ["frc300", "frc301", "frc302"],
            None,
        ),
    ],
)
def test_alliance_name(
    selections: Optional[List[EventAlliance]],
    team_keys: List[TeamKey],
    output: Optional[str],
) -> None:
    name = PlayoffAdvancementHelper._alliance_name(team_keys, selections)
    assert name == output


def test_standard_bracket(test_data_importer) -> None:
    event = create_event("2019nyny", PlayoffType.BRACKET_8_TEAM)
    test_data_importer.import_event_alliances(
        __file__, "data/2019nyny_alliances.json", "2019nyny"
    )
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )
    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_2019nyny.json", "r"
    ) as f:
        expected_advancement = json.load(f)

    assert json.loads(json.dumps(advancement)) == expected_advancement

    apiv3_response = (
        PlayoffAdvancementHelper.create_playoff_advancement_response_for_apiv3(
            event, advancement.playoff_advancement, advancement.bracket_table
        )
    )
    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_apiv3_2019nyny.json",
        "r",
    ) as f:
        expected_advancement_apiv3 = json.load(f)
    assert apiv3_response == expected_advancement_apiv3


def test_2015_event(test_data_importer) -> None:
    event = create_event("2015nyny", PlayoffType.AVG_SCORE_8_TEAM)
    test_data_importer.import_event_alliances(
        __file__, "data/2015nyny_alliances.json", "2015nyny"
    )
    matches = test_data_importer.parse_match_list(
        __file__, "data/2015nyny_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )
    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_2015nyny.json", "r"
    ) as f:
        expected_advancement = json.load(f)

    assert json.loads(json.dumps(advancement)) == expected_advancement

    apiv3_response = (
        PlayoffAdvancementHelper.create_playoff_advancement_response_for_apiv3(
            event, advancement.playoff_advancement, advancement.bracket_table
        )
    )
    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_apiv3_2015nyny.json",
        "r",
    ) as f:
        expected_advancement_apiv3 = json.load(f)
    assert apiv3_response == expected_advancement_apiv3


@pytest.mark.parametrize(
    "event_key", ["2017cmpmo", "2018cmptx", "2019cmptx", "2022cmptx"]
)
def test_round_robin(test_data_importer, event_key) -> None:
    event = create_event(event_key, PlayoffType.ROUND_ROBIN_6_TEAM)
    test_data_importer.import_event_alliances(
        __file__, f"data/{event_key}_alliances.json", event_key
    )
    matches = test_data_importer.parse_match_list(
        __file__, f"data/{event_key}_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )

    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_{event_key}.json", "r"
    ) as f:
        expected_advancement = json.load(f)

    assert json.loads(json.dumps(advancement)) == expected_advancement

    apiv3_response = (
        PlayoffAdvancementHelper.create_playoff_advancement_response_for_apiv3(
            event, advancement.playoff_advancement, advancement.bracket_table
        )
    )
    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_apiv3_{event_key}.json",
        "r",
    ) as f:
        expected_advancement_apiv3 = json.load(f)
    assert apiv3_response == expected_advancement_apiv3


def test_best_of_3_finals(test_data_importer) -> None:
    event = create_event("2019nyny", PlayoffType.BO3_FINALS)
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )
    assert advancement.bracket_table is not None
    assert advancement.playoff_advancement is None
    assert advancement.double_elim_matches is None
    assert advancement.playoff_template is None


def test_best_of_5_finals(test_data_importer) -> None:
    event = create_event("2019nyny", PlayoffType.BO5_FINALS)
    matches = test_data_importer.parse_match_list(
        __file__, "data/2019nyny_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]

    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )
    assert advancement.bracket_table is not None
    assert advancement.playoff_advancement is None
    assert advancement.double_elim_matches is None
    assert advancement.playoff_template is None


def test_legacy_double_elim(test_data_importer) -> None:
    event = create_event("2017wiwi", PlayoffType.LEGACY_DOUBLE_ELIM_8_TEAM)
    matches = test_data_importer.parse_match_list(
        __file__, "data/2017wiwi_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]
    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )
    assert advancement.bracket_table is not None
    assert advancement.playoff_advancement is None
    assert advancement.double_elim_matches is not None
    assert advancement.playoff_template is None


def test_double_elim_8(test_data_importer) -> None:
    event = create_event("2023mijac", PlayoffType.DOUBLE_ELIM_8_TEAM)
    test_data_importer.import_event_alliances(
        __file__, "data/2023mijac_alliances.json", "2023mijac"
    )
    matches = test_data_importer.parse_match_list(
        __file__, "data/2023mijac_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]
    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )

    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_2023mijac.json", "r"
    ) as f:
        expected_advancement = json.load(f)

    assert (
        json.loads(json.dumps(advancement.bracket_table))
        == expected_advancement["bracket"]
    )
    assert (
        json.loads(json.dumps(advancement.playoff_advancement))
        == expected_advancement["advancement"]
    )

    apiv3_response = (
        PlayoffAdvancementHelper.create_playoff_advancement_response_for_apiv3(
            event, advancement.playoff_advancement, advancement.bracket_table
        )
    )
    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_apiv3_2023mijac.json",
        "r",
    ) as f:
        expected_advancement_apiv3 = json.load(f)
    assert json.loads(json.dumps(apiv3_response)) == expected_advancement_apiv3


def test_double_elim_4(test_data_importer) -> None:
    event = create_event("2023micmp", PlayoffType.DOUBLE_ELIM_4_TEAM)
    test_data_importer.import_event_alliances(
        __file__, "data/2023micmp_alliances.json", "2023micmp"
    )
    matches = test_data_importer.parse_match_list(
        __file__, "data/2023micmp_matches.json"
    )
    organized_matches = MatchHelper.organized_matches(matches)[1]
    advancement = PlayoffAdvancementHelper.generate_playoff_advancement(
        event, organized_matches
    )

    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_2023micmp.json", "r"
    ) as f:
        expected_advancement = json.load(f)

    assert (
        json.loads(json.dumps(advancement.bracket_table))
        == expected_advancement["bracket"]
    )
    assert (
        json.loads(json.dumps(advancement.playoff_advancement))
        == expected_advancement["advancement"]
    )

    apiv3_response = (
        PlayoffAdvancementHelper.create_playoff_advancement_response_for_apiv3(
            event, advancement.playoff_advancement, advancement.bracket_table
        )
    )
    with open(
        f"{os.path.dirname(__file__)}/data/expected_advancement_apiv3_2023micmp.json",
        "r",
    ) as f:
        expected_advancement_apiv3 = json.load(f)
    assert json.loads(json.dumps(apiv3_response)) == expected_advancement_apiv3
