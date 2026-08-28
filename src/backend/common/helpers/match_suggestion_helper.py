"""
Ranks upcoming matches across currently-live events for the GameDay match
suggestion feed.

Not to be confused with `match_suggestion_accepter.py`, which is about the
user-submitted Suggestion moderation queue.
"""

import datetime
import math
from typing import Dict, List, Optional, Set, Tuple

from google.appengine.ext import ndb

from backend.common.consts.alliance_color import AllianceColor
from backend.common.consts.comp_level import CompLevel
from backend.common.consts.playoff_type import (
    DOUBLE_ELIM_TYPES,
    DoubleElimRound,
    PlayoffType,
)
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.playoff_type_helper import PlayoffTypeHelper
from backend.common.helpers.team_favorite_counts_helper import TeamFavoriteCountsHelper
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.keys import TeamKey, Year
from backend.common.models.match import Match
from backend.common.models.match_suggestion import (
    MatchSuggestion,
    MatchSuggestionComponents,
    MatchSuggestions,
)
from backend.common.queries.event_query import TeamYearEventsQuery

# Weights sum to 1.0, so the final score also lands in [0, 1]
W_FAVORITES: float = 0.25
W_SIGNIFICANCE: float = 0.25
W_TIME_DECAY: float = 0.25
W_PERFORMANCE: float = 0.25

NUM_SUGGESTIONS: int = 25
MAX_UPCOMING_PER_EVENT: int = 3
MAX_CANDIDATES: int = 250

LEVEL_WEIGHTS: Dict[CompLevel, float] = {
    CompLevel.QM: 0.0,
    CompLevel.EF: 5.0,
    CompLevel.QF: 10.0,
    CompLevel.SF: 20.0,
    CompLevel.F: 50.0,
}
MAX_LEVEL_WEIGHT: float = 50.0

# From 2023 on the whole double elim bracket is `sf`, so the comp level alone
# cannot tell a first-round match from the one deciding the last finals slot.
# These ramp between the flat `sf` weight and `f`.
DOUBLE_ELIM_ROUND_WEIGHTS: Dict[DoubleElimRound, float] = {
    DoubleElimRound.ROUND1: 15.0,
    DoubleElimRound.ROUND2: 20.0,
    DoubleElimRound.ROUND3: 27.0,
    DoubleElimRound.ROUND4: 33.0,
    DoubleElimRound.ROUND5: 40.0,
    DoubleElimRound.FINALS: 50.0,
}

# FUTURE covers matches that have not started yet. A champs match cycle is
# ~7-10 minutes, so a 15 minute e-folding time keeps roughly the next two
# matches per field hot.
#
# PAST covers a match whose time has gone by but which still has no score.
# That is either a match on the field right now -- the most valuable thing we
# can show -- or a dead schedule entry that will never be played. The short
# PAST tau keeps the former hot while the latter fades, and the PAST horizon
# drops anything that overdue from scoring at all.
TIME_DECAY_TAU_FUTURE_S: int = 15 * 60
TIME_DECAY_TAU_PAST_S: int = 5 * 60
TIME_HORIZON_FUTURE_S: int = 3 * 60 * 60
TIME_HORIZON_PAST_S: int = 30 * 60

DEGENERATE_NORMALIZED_VALUE: float = 0.5
EPSILON: float = 1e-9


class MatchSuggestionHelper:
    @classmethod
    def compute_match_suggestions(
        cls,
        events: Optional[List[Event]] = None,
        now: Optional[datetime.datetime] = None,
    ) -> MatchSuggestions:
        """
        Score every upcoming match at the given events and return the top
        `NUM_SUGGESTIONS` of them, ranked best-first.

        `events` and `now` are injectable for testing; by default this uses the
        events that are live right now and the current (naive UTC) time.
        """
        now = now or datetime.datetime.now()

        if events is None:
            events = [e for e in EventHelper.events_within_a_day() if e.now]

        ranked = cls._rank(cls._candidate_matches(events, now), now)
        return MatchSuggestions(
            updated_at=int(now.timestamp()),
            suggestions={s.match_key: s for s in ranked[:NUM_SUGGESTIONS]},
        )

    @classmethod
    def score_all_matches(
        cls,
        events: List[Event],
        now: Optional[datetime.datetime] = None,
    ) -> MatchSuggestions:
        """
        Score every match at the given events, played or not, ignoring the
        schedule entirely.

        A validation tool, not used by the cron. Time decay is forced to 0 so
        that favorites, significance and performance can be compared without a
        scheduling term swamping them -- which also means `score` here tops out
        at the sum of the other three weights rather than 1.0.

        Performance and favorites are still min-max normalized across whatever
        you pass in, so scoring two events together ranks them against each
        other, while scoring them separately does not.
        """
        now = now or datetime.datetime.now()

        for event in events:
            event.prep_matches()
        candidates = [(event, match) for event in events for match in event.matches]

        ranked = cls._rank(candidates, now, time_weighted=False)
        return MatchSuggestions(
            updated_at=int(now.timestamp()),
            suggestions={s.match_key: s for s in ranked},
        )

    @classmethod
    def _rank(
        cls,
        candidates: List[Tuple[Event, Match]],
        now: datetime.datetime,
        time_weighted: bool = True,
    ) -> List[MatchSuggestion]:
        """
        Score every candidate and return them all, best-first, with `rank` assigned.

        Callers truncate; ranks are 0-based over the full list, so slicing a prefix
        leaves them contiguous.

        `time_weighted=False` reports `time_decay` as a flat 0.0 rather than merely
        weighting it away, so that `score_all_matches` publishes a component value
        that matches the score it contributed.
        """
        if not candidates:
            return []

        matches = [match for _, match in candidates]
        team_keys = {
            team_key for match in matches for team_key in cls._match_teams(match)
        }

        oprs = cls.team_recent_oprs(team_keys, matches[0].year, now)
        favorite_counts = TeamFavoriteCountsHelper.get_counts(team_keys)

        raw_performance: List[float] = []
        raw_favorites: List[float] = []
        for match in matches:
            red = sum(
                oprs.get(tk, 0.0) for tk in match.alliances[AllianceColor.RED]["teams"]
            )
            blue = sum(
                oprs.get(tk, 0.0) for tk in match.alliances[AllianceColor.BLUE]["teams"]
            )
            raw_performance.append(cls._performance_kernel(red, blue))
            # log1p because favorite counts are heavy-tailed -- without it a single
            # megastar team would swamp the whole component
            raw_favorites.append(
                sum(
                    math.log1p(favorite_counts.get(tk, 0))
                    for tk in cls._match_teams(match)
                )
            )

        performance = cls._min_max_normalize(raw_performance)
        favorites = cls._min_max_normalize(raw_favorites)

        scored: List[Tuple[float, Event, Match, MatchSuggestionComponents]] = []
        for i, (event, match) in enumerate(candidates):
            components = MatchSuggestionComponents(
                favorites=favorites[i],
                significance=cls._significance(event, match),
                time_decay=(
                    cls._time_decay(match.predicted_time or match.time, now)
                    if time_weighted
                    else 0.0
                ),
                performance=performance[i],
            )
            score = round(
                W_FAVORITES * components.favorites
                + W_SIGNIFICANCE * components.significance
                + W_TIME_DECAY * components.time_decay
                + W_PERFORMANCE * components.performance,
                4,
            )
            scored.append((score, event, match, components))

        # Tiebreak on play order so ranks are stable between runs
        scored.sort(key=lambda s: (-s[0], s[2].key_name))

        return [
            MatchSuggestion(
                match_key=match.key_name,
                event_key=event.key_name,
                event_name=event.name,
                event_short_name=event.short_name,
                comp_level=match.comp_level,
                set_number=match.set_number,
                match_number=match.match_number,
                display_name=match.short_name,
                red_team_numbers=[
                    int(tk[3:]) for tk in match.alliances[AllianceColor.RED]["teams"]
                ],
                blue_team_numbers=[
                    int(tk[3:]) for tk in match.alliances[AllianceColor.BLUE]["teams"]
                ],
                predicted_time=(
                    int(match.predicted_time.timestamp())
                    if match.predicted_time
                    else None
                ),
                scheduled_time=(int(match.time.timestamp()) if match.time else None),
                rank=rank,
                score=score,
                components=components,
            )
            for rank, (score, event, match, components) in enumerate(scored)
        ]

    @classmethod
    def _candidate_matches(
        cls, events: List[Event], now: datetime.datetime
    ) -> List[Tuple[Event, Match]]:
        """
        Unplayed, scheduled, near-term matches from the given events.
        """
        for event in events:
            event.prep_matches()

        candidates: List[Tuple[Event, Match]] = []
        for event in events:
            upcoming = MatchHelper.upcoming_matches(
                event.matches, num=MAX_UPCOMING_PER_EVENT
            )
            for match in upcoming:
                match_time = match.predicted_time or match.time
                if match_time is None:
                    continue
                delta = (match_time - now).total_seconds()
                if -TIME_HORIZON_PAST_S <= delta <= TIME_HORIZON_FUTURE_S:
                    candidates.append((event, match))

        return candidates[:MAX_CANDIDATES]

    @staticmethod
    def _match_teams(match: Match) -> List[TeamKey]:
        return (
            match.alliances[AllianceColor.RED]["teams"]
            + match.alliances[AllianceColor.BLUE]["teams"]
        )

    @staticmethod
    def team_recent_oprs(
        team_keys: Set[TeamKey], year: Year, now: datetime.datetime
    ) -> Dict[TeamKey, float]:
        """
        The most recent non-offseason event OPR for each team, within `year`.

        Walks each team's in-season events newest-first and returns the first OPR
        it finds, rather than reading only the newest event -- during a live event
        the newest event often has no matchstats computed yet. Teams with no
        in-season OPR this year get 0.0.

        Never looks at other years: OPR is in game-score units, so a prior
        season's value is not comparable.
        """
        today = now.date()
        event_futures = {
            team_key: TeamYearEventsQuery(team_key, year).fetch_async()
            for team_key in sorted(team_keys)
        }

        team_events: Dict[TeamKey, List[Event]] = {
            team_key: sorted(
                (
                    event
                    for event in future.get_result()
                    if event.is_in_season
                    and event.start_date is not None
                    and event.start_date.date() <= today
                ),
                key=lambda e: e.start_date,
                reverse=True,
            )
            for team_key, future in event_futures.items()
        }

        # Teams share events heavily, so fetch each event's stats only once
        event_keys = sorted(
            {event.key_name for events in team_events.values() for event in events}
        )
        details = ndb.get_multi([ndb.Key(EventDetails, key) for key in event_keys])
        oprs_by_event = {
            key: ((detail.matchstats if detail else None) or {}).get("oprs") or {}
            for key, detail in zip(event_keys, details)
        }

        oprs: Dict[TeamKey, float] = {}
        for team_key, events in team_events.items():
            # matchstats is keyed by bare team id ("254"), not team key
            team_id = team_key[3:]
            oprs[team_key] = 0.0
            for event in events:
                opr = oprs_by_event[event.key_name].get(team_id)
                if opr is not None:
                    # Early-event fits are near rank-deficient and can go negative
                    oprs[team_key] = max(0.0, opr)
                    break

        return oprs

    @staticmethod
    def _time_decay(
        match_time: Optional[datetime.datetime], now: datetime.datetime
    ) -> float:
        """
        Peaks at 1.0 when the match is starting and decays smoothly either side.

        Deliberately absolute rather than pool-normalized: on a day where every
        candidate is 40 minutes out, normalizing would still hand one of them a
        1.0 and claim it was imminent.
        """
        if match_time is None:
            return 0.0
        delta = (match_time - now).total_seconds()
        if delta >= 0:
            return math.exp(-delta / TIME_DECAY_TAU_FUTURE_S)
        return math.exp(delta / TIME_DECAY_TAU_PAST_S)

    @staticmethod
    def _significance(event: Event, match: Match) -> float:
        """
        How much the match matters, from quals (0.0) up to finals (1.0).

        Also deliberately absolute: min-max normalizing would make quals score
        like finals on a quals-only afternoon.

        2023+ double elim brackets are entirely `sf`, so those matches are placed
        by bracket round instead of by comp level.
        """
        weight = LEVEL_WEIGHTS.get(match.comp_level, 0.0)

        if (
            match.year >= 2023
            and match.comp_level == CompLevel.SF
            and event.playoff_type in DOUBLE_ELIM_TYPES
        ):
            try:
                if event.playoff_type == PlayoffType.DOUBLE_ELIM_4_TEAM:
                    elim_round = PlayoffTypeHelper.get_double_elim_4_round(
                        match.comp_level, match.set_number
                    )
                elif event.playoff_type == PlayoffType.LEGACY_DOUBLE_ELIM_8_TEAM:
                    elim_round = PlayoffTypeHelper.get_double_elim_round_pre_2023(
                        match.comp_level, match.set_number
                    )
                else:
                    elim_round = PlayoffTypeHelper.get_double_elim_round(
                        match.comp_level, match.set_number
                    )
                weight = DOUBLE_ELIM_ROUND_WEIGHTS.get(elim_round, weight)
            except ValueError:
                # Set number outside the bracket shape -- keep the flat weight
                pass

        return weight / MAX_LEVEL_WEIGHT

    @staticmethod
    def _performance_kernel(red_opr_sum: float, blue_opr_sum: float) -> float:
        """
        Favors close, high-scoring matches: (150, 150) beats (250, 50).
        """
        return max(red_opr_sum, blue_opr_sum) + 2 * min(red_opr_sum, blue_opr_sum)

    @staticmethod
    def _min_max_normalize(values: List[float]) -> List[float]:
        """
        When every value is equal there is no signal to extract, so return a
        neutral 0.5 rather than zeroing out or maxing out the whole component.
        Ranking is unaffected either way.
        """
        if not values:
            return []
        low = min(values)
        high = max(values)
        if (high - low) < EPSILON:
            return [DEGENERATE_NORMALIZED_VALUE] * len(values)
        return [(value - low) / (high - low) for value in values]
