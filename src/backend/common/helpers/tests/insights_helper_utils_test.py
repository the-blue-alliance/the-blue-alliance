from backend.common.helpers.insights_helper_utils import (
    create_insight,
    make_insights_from_functions,
    make_leaderboard_args,
    make_leaderboard_from_dict_counts,
    sort_counter_dict,
)
from backend.common.models.insight import Insight


def test_sort_counter_dict_with_team_keys():
    counter = {
        "frc1": 1,
        "frc2": 2,
        "frc3": 3,
        "frc4": 4,
        "frc5": 5,
        "frc6": 3,
    }

    sorted_counter = sort_counter_dict(counter, key_type="team")
    assert sorted_counter == [
        (5, ["frc5"]),
        (4, ["frc4"]),
        (3, ["frc3", "frc6"]),
        (2, ["frc2"]),
        (1, ["frc1"]),
    ]


def test_sort_counter_dict_with_event_keys():
    counter = {"2024mil": 1, "2023dal": 2, "2019nytr": 2, "2018nyut": 4}

    sorted_counter = sort_counter_dict(counter, key_type="event")
    assert sorted_counter == [
        (4, ["2018nyut"]),
        (2, ["2023dal", "2019nytr"]),
        (1, ["2024mil"]),
    ]


def test_sort_counter_dict_with_match_keys():
    counter = {
        "2024mil_qm1": 1,
        "2024mil_qm2": 2,
        "2024mil_qm3": 3,
        "2024mil_qm4": 4,
        "2024mil_qf1": 4,
    }

    sorted_counter = sort_counter_dict(counter, key_type="match")
    assert sorted_counter == [
        (4, ["2024mil_qm4", "2024mil_qf1"]),
        (3, ["2024mil_qm3"]),
        (2, ["2024mil_qm2"]),
        (1, ["2024mil_qm1"]),
    ]


def test_make_leaderboard_from_dict_counts():
    counter = {
        "frc1": 1,
        "frc2": 2,
        "frc3": 3,
        "frc4": 4,
        "frc5": 5,
        "frc6": 3,
    }

    insight = make_leaderboard_from_dict_counts(
        counter, Insight.TYPED_LEADERBOARD_BLUE_BANNERS, 2024
    )
    assert insight.data == {
        "rankings": [
            {"keys": ["frc5"], "value": 5},
            {"keys": ["frc4"], "value": 4},
            {"keys": ["frc3", "frc6"], "value": 3},
            {"keys": ["frc2"], "value": 2},
            {"keys": ["frc1"], "value": 1},
        ],
        "key_type": "team",
    }


def test_make_args_has_no_offseasons(ndb_stub, test_data_importer):
    test_data_importer.import_event(__file__, "data/2019mttd.json")
    test_data_importer.import_match_list(__file__, "data/2019mttd_matches.json")
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    args = make_leaderboard_args()
    args_2019 = [a for a in args if a.year == 2019]

    assert len(args_2019) == 1

    mttd_2019_matches = [
        m for m in args_2019[0].matches if m.key.id().startswith("2019mttd")
    ]

    assert len(mttd_2019_matches) == 0


def test_make_insights_from_fns_only_computes_overall_and_year(
    ndb_stub, test_data_importer
):
    test_data_importer.import_event(__file__, "data/2025isde1.json")
    test_data_importer.import_match_list(__file__, "data/2025isde1_matches.json")
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    insights = make_insights_from_functions(
        2019,
        [
            lambda _: create_insight(data={}, name="test_2019", year=2019),
            lambda _: create_insight(data={}, name="test_overall", year=0),
        ],
    )

    # If it created all the insights, there'd be 2 * len(valid_years)
    assert len(insights) == 4
