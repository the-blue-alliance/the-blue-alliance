from typing import Dict, List

from google.appengine.ext import ndb

from backend.common.helpers.insights_v2.compute import (
    _build_team_district_map,
    build_leaderboard_pair_rankings,
    build_leaderboard_rankings,
    LEADERBOARD_MAX_KEYS_PER_RANKING,
    LeaderboardV2Calculator,
)
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.insight_v2 import (
    InsightCategory,
    InsightV2NameEntry,
    InsightV2Names,
    LeaderboardKeyType,
    LeaderboardRankingV2,
)
from backend.common.models.team import Team


class _StubLeaderboard(LeaderboardV2Calculator):
    """Minimal concrete subclass used to exercise base-class behaviour."""

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.MOST_MATCHES_PLAYED

    @property
    def key_type(self) -> LeaderboardKeyType:
        return "team"

    def _build_rankings(self, counts: Dict[str, int]) -> List[LeaderboardRankingV2]:
        return build_leaderboard_rankings(counts)

    def on_event(self, event: Event) -> None:
        pass


def test_no_data_returns_no_insights() -> None:
    assert _StubLeaderboard().make_insights(2024, {}) == []


def test_rankings_sorted_descending(ndb_stub) -> None:
    calc = _StubLeaderboard()
    calc._increment("frc1", 5)
    calc._increment("frc2", 3)
    calc._increment("frc3", 8)

    assert calc.make_insights(2024, {})[0].data["rankings"] == [
        {"value": 8, "keys": ["frc3"]},
        {"value": 5, "keys": ["frc1"]},
        {"value": 3, "keys": ["frc2"]},
    ]


def test_team_keys_sorted_numerically(ndb_stub) -> None:
    calc = _StubLeaderboard()
    # Same count so all three land in the same ranking group
    calc._increment("frc100", 3)
    calc._increment("frc5", 3)
    calc._increment("frc50", 3)

    assert calc.make_insights(2024, {})[0].data["rankings"] == [
        {"value": 3, "keys": ["frc5", "frc50", "frc100"]},
    ]


def test_district_insight_created(ndb_stub) -> None:
    calc = _StubLeaderboard()
    calc._increment("frc1", 5)
    calc._increment("frc2", 3)

    insights = calc.make_insights(2024, {"frc1": "ne", "frc2": "ne"})

    assert len(insights) == 2
    district_insight = next(i for i in insights if i.district_abbreviation == "ne")
    assert district_insight.year == 2024
    assert district_insight.category == InsightCategory.LEADERBOARD
    assert district_insight.data["rankings"] == [
        {"value": 5, "keys": ["frc1"]},
        {"value": 3, "keys": ["frc2"]},
    ]


def test_district_insight_excludes_non_members(ndb_stub) -> None:
    calc = _StubLeaderboard()
    calc._increment("frc1", 5)
    calc._increment("frc2", 3)  # not in any district

    district_insights = [
        i
        for i in calc.make_insights(2024, {"frc1": "ne"})
        if i.district_abbreviation is not None
    ]
    assert district_insights[0].data["rankings"] == [{"value": 5, "keys": ["frc1"]}]


def test_district_key_name(ndb_stub) -> None:
    calc = _StubLeaderboard()
    calc._increment("frc1", 5)

    assert {i.key_name for i in calc.make_insights(2024, {"frc1": "ne"})} == {
        "2024_v2_leaderboard_most_matches_played",
        "2024_v2_leaderboard_most_matches_played_ne",
    }


def test_rankings_excludes_value_of_one() -> None:
    assert build_leaderboard_rankings({"frc1": 1, "frc2": 2}) == [
        LeaderboardRankingV2(keys=["frc2"], value=2),
    ]


def test_rankings_excludes_groups_exceeding_max_keys() -> None:
    counts = {f"frc{i}": 5 for i in range(LEADERBOARD_MAX_KEYS_PER_RANKING + 1)}
    assert build_leaderboard_rankings(counts) == []


def test_rankings_includes_group_at_max_keys() -> None:
    counts = {f"frc{i}": 5 for i in range(LEADERBOARD_MAX_KEYS_PER_RANKING)}
    result = build_leaderboard_rankings(counts)
    assert len(result) == 1
    assert len(result[0]["keys"]) == LEADERBOARD_MAX_KEYS_PER_RANKING


def test_pair_rankings_excludes_value_of_one() -> None:
    assert build_leaderboard_pair_rankings({"frc1|frc2": 1, "frc3|frc4": 2}) == [
        LeaderboardRankingV2(keys=[["frc3", "frc4"]], value=2),
    ]


def test_pair_rankings_excludes_groups_exceeding_max_keys() -> None:
    counts = {
        f"frc{i}|frc{i + 1}": 5 for i in range(LEADERBOARD_MAX_KEYS_PER_RANKING + 1)
    }
    assert build_leaderboard_pair_rankings(counts) == []


def test_pair_rankings_includes_group_at_max_keys() -> None:
    counts = {f"frc{i}|frc{i + 1}": 5 for i in range(LEADERBOARD_MAX_KEYS_PER_RANKING)}
    result = build_leaderboard_pair_rankings(counts)
    assert len(result) == 1
    assert len(result[0]["keys"]) == LEADERBOARD_MAX_KEYS_PER_RANKING


def test_renamed_district_normalized_to_latest_code(ndb_stub) -> None:
    # Teams whose most recent DistrictTeam record uses the old abbreviation (e.g. "chs")
    # should be normalized to the current abbreviation ("fch") so they are bucketed
    # together with teams whose records already use the new code.
    district_key_old = "2022chs"
    district_key_new = "2024fch"
    District(id=district_key_old, year=2022, abbreviation="chs").put()
    District(id=district_key_new, year=2024, abbreviation="fch").put()

    # frc1 last seen under the old "chs" code
    DistrictTeam(
        id=f"{district_key_old}_frc1",
        team=ndb.Key(Team, "frc1"),
        year=2022,
        district_key=ndb.Key(District, district_key_old),
    ).put()

    # frc2 already on the new "fch" code
    DistrictTeam(
        id=f"{district_key_new}_frc2",
        team=ndb.Key(Team, "frc2"),
        year=2024,
        district_key=ndb.Key(District, district_key_new),
    ).put()

    result = _build_team_district_map()
    # Both teams must map to the canonical "fch" abbreviation, not split across "chs"/"fch"
    assert result == {"frc1": "fch", "frc2": "fch"}


def test_district_uses_most_recent_district_team(ndb_stub) -> None:
    district_key_ont = "2018ont"
    district_key_ne = "2024ne"
    District(id=district_key_ont, year=2018, abbreviation="ont").put()
    District(id=district_key_ne, year=2024, abbreviation="ne").put()
    DistrictTeam(
        id=f"{district_key_ont}_frc1",
        team=ndb.Key(Team, "frc1"),
        year=2018,
        district_key=ndb.Key(District, district_key_ont),
    ).put()
    DistrictTeam(
        id=f"{district_key_ne}_frc1",
        team=ndb.Key(Team, "frc1"),
        year=2024,
        district_key=ndb.Key(District, district_key_ne),
    ).put()

    assert _build_team_district_map() == {"frc1": "ne"}
