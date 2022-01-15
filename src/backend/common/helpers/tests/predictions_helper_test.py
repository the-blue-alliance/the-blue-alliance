import json

import pytest
from google.appengine.ext import ndb

from backend.common.consts.alliance_color import AllianceColor
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.prediction_helper import PredictionHelper
from backend.common.models.event import Event
from backend.common.models.keys import EventKey
from backend.common.models.match import Match


@pytest.mark.parametrize(
    "event_key",
    [
        "2020scmb",
        "2019nyny",
        "2018nyny",
        "2017nyny",
        "2016nyny",
    ],
)
def test_compute_match_predictions(event_key: EventKey, test_data_importer) -> None:
    test_data_importer.import_event(__file__, f"data/{event_key}.json")
    test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")

    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()
    sorted_matches = MatchHelper.play_order_sorted_matches(matches)
    (
        match_predictions,
        match_prediction_stats,
        stat_mean_vars,
    ) = PredictionHelper.get_match_predictions(sorted_matches)

    assert match_predictions is not None
    assert match_prediction_stats is not None
    assert stat_mean_vars is not None


def test_past_event_seeds_match_predictions(test_data_importer) -> None:
    test_data_importer.import_event(__file__, "data/2019scmb.json")
    test_data_importer.import_event_predictions(
        __file__, "data/2019scmb_predictions.json", "2019scmb"
    )
    test_data_importer.import_event(__file__, "data/2019nyny.json")
    test_data_importer.import_match_list(__file__, "data/2019nyny_matches.json")

    matches = Match.query(Match.event == ndb.Key(Event, "2019nyny")).fetch()
    sorted_matches = MatchHelper.play_order_sorted_matches(matches)
    (
        match_predictions,
        match_prediction_stats,
        stat_mean_vars,
    ) = PredictionHelper.get_match_predictions(sorted_matches)

    assert match_predictions is not None
    assert match_prediction_stats is not None
    assert stat_mean_vars is not None


@pytest.mark.parametrize(
    "event_key",
    [
        "2020scmb",
        "2019nyny",
        "2018nyny",
        "2017nyny",
        "2016nyny",
    ],
)
def test_compute_rankings_predictions(event_key: EventKey, test_data_importer) -> None:
    test_data_importer.import_event(__file__, f"data/{event_key}.json")
    test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")
    with open(
        test_data_importer._get_path(__file__, f"data/{event_key}_predictions.json"),
        "r",
    ) as f:
        expected_predictions = json.load(f)

    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()
    sorted_matches = MatchHelper.play_order_sorted_matches(matches)
    (
        ranking_predictions,
        ranking_prediction_stats,
    ) = PredictionHelper.get_ranking_predictions(
        sorted_matches, expected_predictions["match_predictions"], n=1
    )

    assert ranking_predictions is not None
    assert ranking_prediction_stats is not None


@pytest.mark.parametrize(
    "event_key",
    [
        "2020scmb",
        "2019nyny",
        "2018nyny",
        "2017nyny",
        "2016nyny",
    ],
)
def test_compute_rankings_predictions_unplayed(
    event_key: EventKey, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, f"data/{event_key}.json")
    test_data_importer.import_match_list(__file__, f"data/{event_key}_matches.json")
    with open(
        test_data_importer._get_path(__file__, f"data/{event_key}_predictions.json"),
        "r",
    ) as f:
        expected_predictions = json.load(f)

    matches = Match.query(Match.event == ndb.Key(Event, event_key)).fetch()
    sorted_matches = MatchHelper.play_order_sorted_matches(matches)

    def mark_unplayed(match: Match):
        alliances = match.alliances
        alliances[AllianceColor.RED]["score"] = -1
        alliances[AllianceColor.BLUE]["score"] = -1
        match.alliances_json = json.dumps(alliances)
        match._alliances = None

    mark_unplayed(matches[-1])

    (
        ranking_predictions,
        ranking_prediction_stats,
    ) = PredictionHelper.get_ranking_predictions(
        sorted_matches, expected_predictions["match_predictions"], n=1
    )

    assert ranking_predictions is not None
    assert ranking_prediction_stats is not None
