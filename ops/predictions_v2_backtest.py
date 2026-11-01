"""Backtest the predictions_v2 model on TBA APIv3 JSON.

The data directory holds one folder per season: ``<year>/events.json`` (the event list) and
``<year>/matches/<event_key>.json`` (each event's matches), in APIv3 format, for example
fetched with tba-cli.

The model replays every season from ``--first-year`` in order (seasons carry over), and the
pre-match predictions of the ``--score`` seasons are scored. ``--v1`` also scores the v1
predictor on the same matches.

    uv run python ops/predictions_v2_backtest.py --data DIR --score 2025,2026 --v1
"""

import argparse
import copy
import glob
import json
import os
import sys
import time
from typing import Dict, Iterator, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from google.appengine.ext import ndb, testbed  # noqa: E402

from backend.common.helpers.predictions_v2.adapter import (  # noqa: E402
    build_stream,
    EntryKind,
    StreamItem,
)
from backend.common.helpers.predictions_v2.backtest import (  # noqa: E402
    evaluate,
    v1_metrics,
)
from backend.common.models.event import Event  # noqa: E402
from backend.common.models.keys import EventKey, MatchKey, Year  # noqa: E402
from backend.common.models.match import Match  # noqa: E402
from backend.common.queries.dict_converters.event_converter import (  # noqa: E402
    EventConverter,
)
from backend.common.queries.dict_converters.match_converter import (  # noqa: E402
    MatchConverter,
)


def load_season(data_dir: str, year: Year) -> Tuple[Dict[EventKey, Event], List[Match]]:
    path = os.path.join(data_dir, str(year), "events.json")
    if not os.path.exists(path):
        return {}, []
    with open(path) as f:
        events = {e["key"]: EventConverter.dictToModel_v3(e) for e in json.load(f)}
    ndb.put_multi(list(events.values()))
    matches: List[Match] = []
    for path in sorted(
        glob.glob(os.path.join(data_dir, str(year), "matches", "*.json"))
    ):
        with open(path) as f:
            matches += [
                MatchConverter.dictToModel_v3(copy.deepcopy(m))
                for m in json.load(f) or []
            ]
    return events, matches


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data", required=True)
    ap.add_argument("--first-year", type=int, default=2002)
    ap.add_argument("--last-year", type=int, default=2026)
    ap.add_argument("--score", required=True, help="comma-separated seasons to score")
    ap.add_argument("--v1", action="store_true", help="also score the v1 predictor")
    args = ap.parse_args()
    score_years = {int(y) for y in args.score.split(",")}

    tb = testbed.Testbed()
    tb.activate()
    tb.init_datastore_v3_stub()
    tb.init_memcache_stub()
    ndb.get_context().set_cache_policy(False)

    kept: Dict[EventKey, Event] = {}
    kept_matches: List[Match] = []
    scored: Set[MatchKey] = set()

    def stream() -> Iterator[StreamItem]:
        for year in range(args.first_year, args.last_year + 1):
            t0 = time.time()
            events, matches = load_season(args.data, year)
            items = build_stream(events, matches)
            print(f"{year}: {len(items)} entries", file=sys.stderr)
            if year in score_years:
                kept.update(events)
                kept_matches.extend(matches)
                scored.update(
                    it.context.match_key for it in items if it.kind == EntryKind.TRAIN
                )
            yield from items
            print(f"{year}: done in {time.time() - t0:.0f}s", file=sys.stderr)

    metrics = evaluate(stream(), score_years)
    print("season  matches  brier    log_loss  accuracy  score_mae  rp_brier")
    for y, m in metrics.items():
        rp = f"{m.rp_brier:.4f}" if m.rp_brier is not None else "-"
        print(
            f"{y}    {m.win.matches:7d}  {m.win.brier:.4f}   {m.win.log_loss:.4f}    "
            f"{m.win.accuracy:.4f}    {m.score_mae:7.3f}    {rp}"
        )
    if args.v1:
        for y in sorted(score_years):
            events = {k: e for k, e in kept.items() if e.year == y}
            v1 = v1_metrics(events, kept_matches, scored)
            print(
                f"v1 {y} {v1.matches:7d}  {v1.brier:.4f}   {v1.log_loss:.4f}    {v1.accuracy:.4f}"
            )
    tb.deactivate()


if __name__ == "__main__":
    main()
