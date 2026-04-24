from typing import Dict, List

from google.appengine.ext import ndb

from backend.common.helpers.insights_v2.compute import (
    _build_team_district_map,
    build_leaderboard_rankings,
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

    assert _build_team_district_map(["frc1"]) == {"frc1": "ne"}
