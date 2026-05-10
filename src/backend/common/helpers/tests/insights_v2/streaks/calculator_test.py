from google.appengine.ext import ndb

from backend.common.helpers.insights_v2.names import InsightV2NameEntry, InsightV2Names
from backend.common.helpers.insights_v2.registry import _build_team_district_map
from backend.common.helpers.insights_v2.streaks.calculator import (
    STREAK_TOP_N,
    StreakV2Calculator,
)
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.event import Event
from backend.common.models.insight_v2 import InsightCategory
from backend.common.models.team import Team


class _StubStreak(StreakV2Calculator):
    """Minimal concrete subclass used to exercise base-class behaviour."""

    @property
    def insight_name(self) -> InsightV2NameEntry:
        return InsightV2Names.QUALIFYING_EVENT_WIN_STREAK

    def on_event(self, event: Event) -> None:
        pass


def test_no_data_returns_no_insights() -> None:
    assert _StubStreak().make_insights(2024, {}) == []


def test_advance_streak_builds_entry(ndb_stub) -> None:
    calc = _StubStreak()
    calc._advance_streak("frc1", "2024eve1")
    calc._advance_streak("frc1", "2024eve2")

    entries = calc.make_insights(2024, {})[0].data["entries"]
    assert entries[0]["key"] == "frc1"
    assert entries[0]["key_type"] == "team"
    assert entries[0]["streak_length"] == 2
    assert entries[0]["start"] == "2024eve1"
    assert entries[0]["end"] == "2024eve2"
    assert entries[0]["is_active"] is True


def test_reset_streak_marks_inactive_and_preserves_best(ndb_stub) -> None:
    calc = _StubStreak()
    calc._advance_streak("frc1", "2023eve1")
    calc._advance_streak("frc1", "2023eve2")
    calc._reset_streak("frc1")

    entries = calc.make_insights(2024, {})[0].data["entries"]
    assert entries[0]["streak_length"] == 2
    assert entries[0]["start"] == "2023eve1"
    assert entries[0]["end"] == "2023eve2"
    assert entries[0]["is_active"] is False


def test_team_appears_multiple_times_with_multiple_distinct_streaks(ndb_stub) -> None:
    calc = _StubStreak()
    # frc1 has two separate streaks of length 2
    calc._advance_streak("frc1", "e1")
    calc._advance_streak("frc1", "e2")
    calc._reset_streak("frc1")
    calc._advance_streak("frc1", "e3")
    calc._advance_streak("frc1", "e4")

    entries = calc.make_insights(2024, {})[0].data["entries"]
    assert len(entries) == 2
    assert all(e["key"] == "frc1" for e in entries)
    assert entries[0]["streak_length"] == 2
    assert entries[0]["start"] == "e1"
    assert entries[0]["end"] == "e2"
    assert entries[0]["is_active"] is False
    assert entries[1]["streak_length"] == 2
    assert entries[1]["start"] == "e3"
    assert entries[1]["end"] == "e4"
    assert entries[1]["is_active"] is True


def test_team_completed_and_active_streaks_both_appear(ndb_stub) -> None:
    calc = _StubStreak()
    # frc1 completes a streak of 3, then starts a new streak of 2
    calc._advance_streak("frc1", "e1")
    calc._advance_streak("frc1", "e2")
    calc._advance_streak("frc1", "e3")
    calc._reset_streak("frc1")
    calc._advance_streak("frc1", "e4")
    calc._advance_streak("frc1", "e5")
    # frc2 has a single active streak of 2
    calc._advance_streak("frc2", "e1")
    calc._advance_streak("frc2", "e2")

    entries = calc.make_insights(2024, {})[0].data["entries"]
    # frc1's length-3 streak comes first, then frc2 and frc1 at length 2
    assert entries[0]["key"] == "frc1"
    assert entries[0]["streak_length"] == 3
    assert entries[0]["is_active"] is False
    # The two length-2 entries sorted by team number (frc1 < frc2), then start
    length_2 = [e for e in entries if e["streak_length"] == 2]
    assert length_2[0]["key"] == "frc1"
    assert length_2[1]["key"] == "frc2"


def test_entries_sorted_by_length_then_team_number(ndb_stub) -> None:
    calc = _StubStreak()
    calc._advance_streak("frc100", "e1")
    calc._advance_streak("frc5", "e1")
    calc._advance_streak("frc5", "e2")

    entries = calc.make_insights(2024, {})[0].data["entries"]
    assert [e["key"] for e in entries] == ["frc5", "frc100"]


def test_entries_with_equal_length_sorted_by_team_number(ndb_stub) -> None:
    calc = _StubStreak()
    for team in ["frc100", "frc5", "frc50"]:
        calc._advance_streak(team, "e1")

    entries = calc.make_insights(2024, {})[0].data["entries"]
    assert [e["key"] for e in entries] == ["frc5", "frc50", "frc100"]


def test_global_top_n_truncates(ndb_stub) -> None:
    calc = _StubStreak()
    for i in range(STREAK_TOP_N + 5):
        calc._advance_streak(f"frc{i + 1}", "e1")

    entries = calc.make_insights(2024, {})[0].data["entries"]
    assert len(entries) == STREAK_TOP_N


def test_district_insight_created(ndb_stub) -> None:
    calc = _StubStreak()
    calc._advance_streak("frc1", "e1")
    calc._advance_streak("frc1", "e2")
    calc._advance_streak("frc2", "e1")

    insights = calc.make_insights(2024, {"frc1": "ne", "frc2": "ne"})
    assert len(insights) == 2
    district_insight = next(i for i in insights if i.district_abbreviation == "ne")
    assert [e["key"] for e in district_insight.data["entries"]] == ["frc1", "frc2"]


def test_district_top_n_independent_of_global_top_n(ndb_stub) -> None:
    calc = _StubStreak()
    # Fill the global top-N with non-district teams at streak length 3
    for i in range(STREAK_TOP_N):
        for label in ["e1", "e2", "e3"]:
            calc._advance_streak(f"frc{9000 + i}", label)
    # District team with streak 2 ranks outside the global top-N
    calc._advance_streak("frc1", "e1")
    calc._advance_streak("frc1", "e2")

    insights = calc.make_insights(2024, {"frc1": "ne"})
    global_insight = next(i for i in insights if i.district_abbreviation is None)
    district_insight = next(i for i in insights if i.district_abbreviation == "ne")

    assert "frc1" not in [e["key"] for e in global_insight.data["entries"]]
    assert district_insight.data["entries"][0]["key"] == "frc1"


def test_insight_category_is_streak(ndb_stub) -> None:
    calc = _StubStreak()
    calc._advance_streak("frc1", "e1")
    assert calc.make_insights(2024, {})[0].category == InsightCategory.STREAK


def test_key_name(ndb_stub) -> None:
    calc = _StubStreak()
    calc._advance_streak("frc1", "e1")
    insights = calc.make_insights(2024, {"frc1": "ne"})
    assert {i.key_name for i in insights} == {
        "2024_v2_streak_qualifying_event_win_streak",
        "2024_v2_streak_qualifying_event_win_streak_ne",
    }


def test_renamed_district_normalized_to_latest_code(ndb_stub) -> None:
    # frc1 last seen under the old "chs" code; frc2 already on the renamed "fch" code.
    # Both teams should be grouped into a single district insight under "fch".
    District(id="2022chs", year=2022, abbreviation="chs").put()
    District(id="2024fch", year=2024, abbreviation="fch").put()
    DistrictTeam(
        id="2022chs_frc1",
        team=ndb.Key(Team, "frc1"),
        year=2022,
        district_key=ndb.Key(District, "2022chs"),
    ).put()
    DistrictTeam(
        id="2024fch_frc2",
        team=ndb.Key(Team, "frc2"),
        year=2024,
        district_key=ndb.Key(District, "2024fch"),
    ).put()

    calc = _StubStreak()
    calc._advance_streak("frc1", "e1")
    calc._advance_streak("frc1", "e2")
    calc._advance_streak("frc2", "e1")

    team_to_district = _build_team_district_map()
    insights = calc.make_insights(2024, team_to_district)

    district_insights = [i for i in insights if i.district_abbreviation is not None]
    assert len(district_insights) == 1
    assert district_insights[0].district_abbreviation == "fch"
    assert {e["key"] for e in district_insights[0].data["entries"]} == {"frc1", "frc2"}
