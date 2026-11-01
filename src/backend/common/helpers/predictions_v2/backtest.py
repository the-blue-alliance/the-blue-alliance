"""Offline backtest: replay a match stream and score the pre-match predictions.

Every training entry is predicted from the state before its result, then learned. The
scores per season are the Brier score, log loss and accuracy of the red win probability
(ties count as 0.5), the score MAE of the PMF means, and the Brier score of the bonus RP
probabilities. ``v1_metrics`` scores the v1 predictor on the same matches.
"""

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Collection, Dict, Iterable, List, Mapping, Optional

from backend.common.consts.alliance_color import AllianceColor
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.prediction_helper import PredictionHelper
from backend.common.helpers.predictions_v2.adapter import EntryKind, StreamItem
from backend.common.helpers.predictions_v2.model.predictor import HKFPredictor
from backend.common.helpers.predictions_v2.model.types import MatchPrediction
from backend.common.models.event import Event
from backend.common.models.keys import EventKey, MatchKey, Year
from backend.common.models.match import Match

# Seasons the v1 predictor supports.
V1_YEARS = frozenset({2016, 2017, 2018, 2019, 2020, 2022, 2023, 2024, 2025, 2026})


@dataclass(frozen=True)
class WinMetrics:
    matches: int
    brier: float
    log_loss: float
    accuracy: float  # decided matches only


@dataclass(frozen=True)
class SeasonMetrics:
    year: Year
    win: WinMetrics
    score_mae: float
    rp_brier: Optional[float]


class _WinAcc:
    def __init__(self) -> None:
        self.n = 0
        self.brier = 0.0
        self.log_loss = 0.0
        self.correct = 0
        self.decided = 0

    def add(self, p_red: float, red_win: float) -> None:
        p = min(max(p_red, 1e-6), 1.0 - 1e-6)
        self.n += 1
        self.brier += (p_red - red_win) ** 2
        self.log_loss -= red_win * math.log(p) + (1.0 - red_win) * math.log(1.0 - p)
        if red_win != 0.5:
            self.decided += 1
            self.correct += (p_red > 0.5) == (red_win == 1.0)

    def result(self) -> WinMetrics:
        n = max(self.n, 1)
        return WinMetrics(
            matches=self.n,
            brier=self.brier / n,
            log_loss=self.log_loss / n,
            accuracy=self.correct / max(self.decided, 1),
        )


def replay(
    stream: Iterable[StreamItem],
    model: Optional[HKFPredictor] = None,
    on_prediction: Optional[Callable[[StreamItem, MatchPrediction], None]] = None,
) -> HKFPredictor:
    """Predict every entry, then learn from the training entries.

    The model rolls over into a season at the season's first training entry. A
    forecast-only entry before that is predicted by a rolled-over copy, so a season
    without training entries (2021) does not roll the model over.
    """
    model = model or HKFPredictor()
    rolled: Optional[HKFPredictor] = None
    for item in stream:
        if item.kind == EntryKind.TRAIN and model.season != item.year:
            model.start_season(item.year)
            rolled = None
        predictor = model
        if model.season != item.year:
            if rolled is None or rolled.season != item.year:
                rolled = HKFPredictor.decode_state(model.encode_state())
                rolled.start_season(item.year)
            predictor = rolled
        pred = predictor.predict_match(item.context)
        if on_prediction is not None:
            on_prediction(item, pred)
        if item.kind == EntryKind.TRAIN:
            model.update(item.context, item.outcome)
    return model


def evaluate(
    stream: Iterable[StreamItem], score_years: Collection[Year]
) -> Dict[Year, SeasonMetrics]:
    win: Dict[Year, _WinAcc] = defaultdict(_WinAcc)
    score_err: Dict[Year, List[float]] = defaultdict(list)
    rp_err: Dict[Year, List[float]] = defaultdict(list)

    def score(item: StreamItem, pred: MatchPrediction) -> None:
        if item.kind != EntryKind.TRAIN or item.year not in score_years:
            return
        o = item.outcome
        win[item.year].add(pred.red_win_prob, o.red_win)
        score_err[item.year].append(abs(pred.red_score.mean - o.red_score))
        score_err[item.year].append(abs(pred.blue_score.mean - o.blue_score))
        for rp, labels in (
            (pred.red_rp, o.red_bonus_rps),
            (pred.blue_rp, o.blue_bonus_rps),
        ):
            if rp is None:
                continue
            for k, y in labels.items():
                q = rp.bonus_rp_probs.get(k)
                if q is not None:
                    rp_err[item.year].append((q - y) ** 2)

    replay(stream, on_prediction=score)
    return {
        y: SeasonMetrics(
            year=y,
            win=acc.result(),
            score_mae=sum(score_err[y]) / max(len(score_err[y]), 1),
            rp_brier=sum(rp_err[y]) / len(rp_err[y]) if rp_err[y] else None,
        )
        for y, acc in sorted(win.items())
    }


def v1_metrics(
    events: Mapping[EventKey, Event],
    matches: Iterable[Match],
    keys: Collection[MatchKey],
) -> WinMetrics:
    """The v1 predictor's win metrics on the matches in ``keys``.

    v1 predicts each match of an event from the event's earlier matches only.
    """
    by_event: Dict[EventKey, List[Match]] = defaultdict(list)
    for m in matches:
        event = events.get(m.event_key_name)
        if event is not None and event.year in V1_YEARS:
            by_event[m.event_key_name].append(m)
    acc = _WinAcc()
    for event_matches in by_event.values():
        ordered = MatchHelper.play_order_sorted_matches(event_matches)
        predictions, _, _ = PredictionHelper.get_match_predictions(ordered)
        if predictions is None:
            continue
        for m in ordered:
            level = "qual" if m.comp_level == "qm" else "playoff"
            pred = predictions[level].get(m.key_name)
            if m.key_name not in keys or pred is None or not m.has_been_played:
                continue
            p = (
                pred["prob"]
                if pred["winning_alliance"] == AllianceColor.RED
                else 1.0 - pred["prob"]
            )
            winner = m.winning_alliance
            red_win = (
                1.0
                if winner == AllianceColor.RED
                else (0.0 if winner == AllianceColor.BLUE else 0.5)
            )
            acc.add(float(p), red_win)
    return acc.result()
