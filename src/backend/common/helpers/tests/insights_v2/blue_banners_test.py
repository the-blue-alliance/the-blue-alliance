from google.appengine.ext import ndb

from backend.common.helpers.insights_v2.blue_banners import BlueBannersV2Calculator
from backend.common.helpers.insights_v2.compute import compute_insights_for_year
from backend.common.models.district import District
from backend.common.models.district_team import DistrictTeam
from backend.common.models.insight_v2 import InsightCategory
from backend.common.models.team import Team


def make_district_team(team_key: str, year: int, district_abbrev: str) -> None:
    district_key = f"{year}{district_abbrev}"
    District(id=district_key, year=year, abbreviation=district_abbrev).put()
    DistrictTeam(
        id=f"{district_key}_{team_key}",
        team=ndb.Key(Team, team_key),
        year=year,
        district_key=ndb.Key(District, district_key),
    ).put()


def test_no_events_returns_empty(ndb_stub) -> None:
    insights = compute_insights_for_year(2024, [BlueBannersV2Calculator()])
    assert insights == []


def test_blue_banners_year(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")

    insights = compute_insights_for_year(2024, [BlueBannersV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.name == "blue_banners"
    assert insight.display_name == "Total Blue Banners"
    assert insight.year == 2024
    assert insight.category == InsightCategory.LEADERBOARD
    assert insight.data["key_type"] == "team"
    rankings = insight.data["rankings"]
    assert len(rankings) > 0
    # All values should be positive integers
    for r in rankings:
        assert r["value"] > 0
        assert len(r["keys"]) > 0


def test_blue_banners_overall(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2019nyny.json")
    test_data_importer.import_award_list(__file__, "../data/2019nyny_awards.json")

    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")

    insights = compute_insights_for_year(0, [BlueBannersV2Calculator()])

    assert len(insights) == 1
    insight = insights[0]
    assert insight.year == 0
    # frc1796 wins at both 2019nyny and 2024nytr so should have 2 banners overall
    rankings = insight.data["rankings"]
    top = rankings[0]
    assert top["value"] == 2
    assert "frc1796" in top["keys"]


def test_blue_banners_rankings_sorted_descending(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2019nyny.json")
    test_data_importer.import_award_list(__file__, "../data/2019nyny_awards.json")

    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")

    insights = compute_insights_for_year(0, [BlueBannersV2Calculator()])
    rankings = insights[0].data["rankings"]

    values = [r["value"] for r in rankings]
    assert values == sorted(values, reverse=True)


def test_blue_banners_team_keys_sorted_numerically(
    ndb_stub, test_data_importer
) -> None:
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")

    insights = compute_insights_for_year(2024, [BlueBannersV2Calculator()])
    rankings = insights[0].data["rankings"]

    for ranking in rankings:
        keys = ranking["keys"]
        nums = [int(k[3:]) for k in keys]
        assert nums == sorted(nums)


def test_key_name(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")

    insights = compute_insights_for_year(2024, [BlueBannersV2Calculator()])
    assert insights[0].key_name == "2024_v2_leaderboard_blue_banners"


def test_district_insight_created(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2022on305.json")
    test_data_importer.import_award_list(__file__, "../data/2022on305_awards.json")
    # Winner teams are frc2200, frc610, frc4015 — register them in the ont district
    for team_key in ("frc2200", "frc610", "frc4015"):
        make_district_team(team_key, 2022, "ont")

    insights = compute_insights_for_year(2022, [BlueBannersV2Calculator()])

    # global insight + one district insight
    assert len(insights) == 2
    district_insight = next(i for i in insights if i.district_abbreviation == "ont")
    assert district_insight.year == 2022
    assert district_insight.name == "blue_banners"
    assert district_insight.category == InsightCategory.LEADERBOARD
    assert district_insight.key_name == "2022_v2_leaderboard_blue_banners_ont"
    rankings = district_insight.data["rankings"]
    assert len(rankings) > 0
    winner_keys = {"frc2200", "frc610", "frc4015"}
    ranked_keys = {k for r in rankings for k in r["keys"]}
    assert winner_keys <= ranked_keys


def test_district_insight_uses_team_membership_not_event_type(
    ndb_stub, test_data_importer
) -> None:
    # 2024nytr is a regional, but frc1796 is registered as a ne district team.
    # Their banner should appear in the ne district insight.
    # frc1591, frc3181, frc9624 also win at 2024nytr but are not district members —
    # they should not appear in any district insight.
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")
    make_district_team("frc1796", 2024, "ne")

    insights = compute_insights_for_year(2024, [BlueBannersV2Calculator()])

    district_insights = [i for i in insights if i.district_abbreviation is not None]
    assert len(district_insights) == 1
    assert district_insights[0].district_abbreviation == "ne"

    ranked_keys = {k for r in district_insights[0].data["rankings"] for k in r["keys"]}
    assert "frc1796" in ranked_keys
    assert "frc1591" not in ranked_keys
    assert "frc3181" not in ranked_keys


def test_district_uses_most_recent_district_team(ndb_stub, test_data_importer) -> None:
    # frc1796 won in 2019 (ne district in 2019) and 2024 (ne district in 2024).
    # They also have an older record in ont from 2018.
    # Their most recent DistrictTeam is 2024 ne, so all their banners count toward ne.
    test_data_importer.import_event(__file__, "../data/2019nyny.json")
    test_data_importer.import_award_list(__file__, "../data/2019nyny_awards.json")
    test_data_importer.import_event(__file__, "../data/2024nytr.json")
    test_data_importer.import_award_list(__file__, "../data/2024nytr_awards.json")
    make_district_team("frc1796", 2018, "ont")
    make_district_team("frc1796", 2024, "ne")

    insights = compute_insights_for_year(0, [BlueBannersV2Calculator()])

    district_insights = [i for i in insights if i.district_abbreviation is not None]
    abbrevs = {i.district_abbreviation for i in district_insights}
    assert "ne" in abbrevs
    assert "ont" not in abbrevs

    ne_insight = next(i for i in district_insights if i.district_abbreviation == "ne")
    ranked_keys = {k for r in ne_insight.data["rankings"] for k in r["keys"]}
    assert "frc1796" in ranked_keys


def test_district_key_name(ndb_stub, test_data_importer) -> None:
    test_data_importer.import_event(__file__, "../data/2022on305.json")
    test_data_importer.import_award_list(__file__, "../data/2022on305_awards.json")
    for team_key in ("frc2200", "frc610", "frc4015"):
        make_district_team(team_key, 2022, "ont")

    insights = compute_insights_for_year(2022, [BlueBannersV2Calculator()])
    key_names = {i.key_name for i in insights}
    assert "2022_v2_leaderboard_blue_banners" in key_names
    assert "2022_v2_leaderboard_blue_banners_ont" in key_names
