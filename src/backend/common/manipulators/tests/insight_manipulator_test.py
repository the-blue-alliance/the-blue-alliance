import json

import pytest
from pyre_extensions import none_throws

from backend.common.manipulators.insight_manipulator import InsightManipulator
from backend.common.models.insight import Insight
from backend.common.queries.insight_query import (
    InsightsLeaderboardsYearQuery,
    InsightsNotablesYearQuery,
)


@pytest.fixture
def old_insight() -> Insight:
    return Insight(
        id=Insight.render_key_name(2024, "test_insight"),
        name="test_insight",
        year=2024,
        data_json=json.dumps({"value": 1}),
    )


@pytest.fixture
def new_insight() -> Insight:
    return Insight(
        id=Insight.render_key_name(2024, "test_insight"),
        name="test_insight",
        year=2024,
        data_json=json.dumps({"value": 2}),
    )


@pytest.mark.usefixtures("ndb_context", "taskqueue_stub")
def test_createOrUpdate(old_insight: Insight, new_insight: Insight) -> None:
    InsightManipulator.createOrUpdate(old_insight)
    assert none_throws(Insight.get_by_id(old_insight.key_name)).data == {"value": 1}

    InsightManipulator.createOrUpdate(new_insight)
    assert none_throws(Insight.get_by_id(old_insight.key_name)).data == {"value": 2}


@pytest.mark.usefixtures("ndb_context")
def test_findOrSpawn(old_insight: Insight, new_insight: Insight) -> None:
    old_insight.put()
    merged = InsightManipulator.findOrSpawn(new_insight)
    assert merged.data == {"value": 2}


@pytest.mark.usefixtures("ndb_context")
def test_updateMerge(old_insight: Insight, new_insight: Insight) -> None:
    merged = InsightManipulator.updateMerge(new_insight, old_insight)
    assert merged is old_insight
    assert merged.data == {"value": 2}
    assert merged._updated_attrs == {"data_json"}


@pytest.mark.usefixtures("ndb_context")
def test_updateMerge_keeps_old_data_when_new_is_empty(old_insight: Insight) -> None:
    merged = InsightManipulator.updateMerge(
        Insight(id=old_insight.key_name, name="test_insight", year=2024), old_insight
    )
    assert merged.data == {"value": 1}


def test_getCacheKeysAndQueries() -> None:
    cache_keys_and_queries = InsightManipulator.getCacheKeysAndQueries(
        {"name": {"test_insight"}, "year": {2024}, "district_abbreviation": set()}
    )
    queries = {query for _, query in cache_keys_and_queries}
    assert queries == {InsightsLeaderboardsYearQuery, InsightsNotablesYearQuery}
