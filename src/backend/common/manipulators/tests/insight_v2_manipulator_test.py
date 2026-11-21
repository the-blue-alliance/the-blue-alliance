import pytest
from pyre_extensions import none_throws

from backend.common.manipulators.insight_v2_manipulator import InsightV2Manipulator
from backend.common.models.insight_v2 import InsightCategory, InsightV2
from backend.common.queries.insight_v2_query import (
    InsightV2YearCategoryQuery,
    InsightV2YearQuery,
)


@pytest.fixture
def old_insight() -> InsightV2:
    return InsightV2(
        id=InsightV2.render_key_name(2024, InsightCategory.LEADERBOARD, "test"),
        name="test",
        display_name="Test",
        year=2024,
        category=InsightCategory.LEADERBOARD,
        data_json={"value": 1},
    )


@pytest.fixture
def new_insight() -> InsightV2:
    return InsightV2(
        id=InsightV2.render_key_name(2024, InsightCategory.LEADERBOARD, "test"),
        name="test",
        display_name="Test",
        year=2024,
        category=InsightCategory.LEADERBOARD,
        data_json={"value": 2},
    )


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
def test_createOrUpdate(old_insight: InsightV2, new_insight: InsightV2) -> None:
    InsightV2Manipulator.createOrUpdate(old_insight)
    assert none_throws(InsightV2.get_by_id(old_insight.key_name)).data == {"value": 1}

    InsightV2Manipulator.createOrUpdate(new_insight)
    assert none_throws(InsightV2.get_by_id(old_insight.key_name)).data == {"value": 2}


@pytest.mark.usefixtures("ndb_context")
def test_findOrSpawn(old_insight: InsightV2, new_insight: InsightV2) -> None:
    old_insight.put()
    merged = InsightV2Manipulator.findOrSpawn(new_insight)
    assert merged.data == {"value": 2}


@pytest.mark.usefixtures("ndb_context")
def test_updateMerge(old_insight: InsightV2, new_insight: InsightV2) -> None:
    merged = InsightV2Manipulator.updateMerge(new_insight, old_insight)
    assert merged is old_insight
    assert merged.data == {"value": 2}
    assert merged._updated_attrs == {"data_json"}


def test_getCacheKeysAndQueries() -> None:
    cache_keys_and_queries = InsightV2Manipulator.getCacheKeysAndQueries(
        {
            "name": {"test"},
            "year": {2024},
            "category": {InsightCategory.LEADERBOARD},
            "district_abbreviation": set(),
        }
    )
    queries = {query for _, query in cache_keys_and_queries}
    assert queries == {InsightV2YearQuery, InsightV2YearCategoryQuery}
