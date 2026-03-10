import json
from typing import Any, Dict, Generator, List, Optional, Set

import pytest
import six
from google.appengine.ext import ndb
from pyre_extensions import none_throws

from backend.common.cache_clearing.get_affected_queries import TCacheKeyAndQuery
from backend.common.consts.api_version import ApiMajorVersion
from backend.common.helpers.deferred import run_from_task
from backend.common.manipulators.manipulator_base import ManipulatorBase, TUpdatedModel
from backend.common.models.cached_model import CachedModel, TAffectedReferences
from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.queries.database_query import CachedDatabaseQuery
from backend.common.queries.dict_converters.converter_base import ConverterBase


class ManipulatorDummyModel(CachedModel):
    int_prop: Optional[int] = ndb.IntegerProperty()
    str_prop: str = ndb.StringProperty()
    mutable_str_prop: str = ndb.StringProperty()
    can_be_none: Optional[int] = ndb.IntegerProperty()
    repeated_prop: List[int] = ndb.IntegerProperty(repeated=True)  # pyre-ignore[8]
    union_prop: List[int] = ndb.IntegerProperty(repeated=True)  # pyre-ignore[8]

    prop_json: str = ndb.StringProperty()

    _mutable_attrs: Set[str] = {
        "int_prop",
        "can_be_none",
        "mutable_str_prop",
    }

    _allow_none_attrs: Set[str] = {
        "can_be_none",
    }

    _list_attrs: Set[str] = {
        "repeated_prop",
    }

    _json_attrs: Set[str] = {
        "prop_json",
    }

    _auto_union_attrs: Set[str] = {
        "union_prop",
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._prop = None

        self._affected_references = {
            "key": set(),
        }

    @property
    def prop(self) -> Dict:
        if self._prop is None and self.prop_json is not None:
            self._prop = json.loads(self.prop_json)
        return self._prop


class DummyConverter(ConverterBase):
    SUBVERSIONS = {
        ApiMajorVersion.API_V3: 0,
    }


class DummyCachedQuery(CachedDatabaseQuery[ManipulatorDummyModel, None]):
    CACHE_VERSION = 0
    CACHE_KEY_FORMAT = "dummy_query_{model_key}"
    CACHE_WRITES_ENABLED = True
    DICT_CONVERTER = DummyConverter

    @ndb.tasklet
    def _query_async(
        self, model_key: str
    ) -> Generator[Any, Any, ManipulatorDummyModel]:
        model = yield ManipulatorDummyModel.get_by_id_async(model_key)
        return model


class DummyManipulator(ManipulatorBase[ManipulatorDummyModel]):
    delete_calls = 0
    delete_hook_extra = None

    update_calls = 0
    update_hook_extra = None

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[TCacheKeyAndQuery]:
        ref_keys: Set[ndb.Key] = affected_refs["key"]
        return [
            (
                none_throws(
                    DummyCachedQuery(model_key=none_throws(k.string_id())).cache_key
                ),
                DummyCachedQuery,
            )
            for k in ref_keys
        ]

    @classmethod
    def updateMerge(
        cls,
        new_model: ManipulatorDummyModel,
        old_model: ManipulatorDummyModel,
        auto_union: bool,
        update_manual_attrs: bool,
    ) -> ManipulatorDummyModel:
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)
        return old_model


class ManipulatorDummyModelWithRequiredProp(CachedModel):
    required_prop: Optional[str] = ndb.StringProperty(required=True)

    _mutable_attrs: Set[str] = {
        "required_prop",
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._affected_references = {
            "key": set(),
        }


class DummyRequiredManipulator(ManipulatorBase[ManipulatorDummyModelWithRequiredProp]):
    update_merge_calls = 0

    @classmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[TCacheKeyAndQuery]:
        return []

    @classmethod
    def updateMerge(
        cls,
        new_model: ManipulatorDummyModelWithRequiredProp,
        old_model: ManipulatorDummyModelWithRequiredProp,
        auto_union: bool,
        update_manual_attrs: bool,
    ) -> ManipulatorDummyModelWithRequiredProp:
        cls.update_merge_calls += 1
        cls._update_attrs(new_model, old_model, auto_union, update_manual_attrs)
        return old_model


@DummyManipulator.register_post_delete_hook
def post_delete_hook(models: List[ManipulatorDummyModel]) -> None:
    DummyManipulator.delete_calls += 1

    if DummyManipulator.delete_hook_extra is not None:
        DummyManipulator.delete_hook_extra(models)


@DummyManipulator.register_post_update_hook
def post_update_hook(models: List[TUpdatedModel[ManipulatorDummyModel]]) -> None:
    DummyManipulator.update_calls += 1

    if DummyManipulator.update_hook_extra is not None:
        DummyManipulator.update_hook_extra(models)


@pytest.fixture(autouse=True)
def reset_hook_call_counts():
    # This prevents counts from leaking between tests, since the classvar is static
    DummyManipulator.delete_calls = 0
    DummyManipulator.delete_hook_extra = None
    DummyManipulator.update_calls = 0
    DummyManipulator.update_hook_extra = None
    DummyRequiredManipulator.update_merge_calls = 0


def test_create_new_model(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=42)
    put = DummyManipulator.createOrUpdate(model)
    assert put == model
    assert put._is_new is True

    check = ManipulatorDummyModel.get_by_id("test")
    assert check == model


def test_create_new_model_list(ndb_context, taskqueue_stub) -> None:
    model1 = ManipulatorDummyModel(id="test1", int_prop=42)
    model2 = ManipulatorDummyModel(id="test2", int_prop=1337)
    put = DummyManipulator.createOrUpdate([model1, model2])
    assert put == [model1, model2]
    assert all(p._is_new for p in put)

    check1 = ManipulatorDummyModel.get_by_id("test1")
    check2 = ManipulatorDummyModel.get_by_id("test2")
    assert [check1, check2] == [model1, model2]


def test_update_model(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=42)
    model.put()

    model.int_prop = 1337
    expected = ManipulatorDummyModel(
        id="test",
        int_prop=1337,
    )
    put = DummyManipulator.createOrUpdate(model)
    assert put == expected

    check = ManipulatorDummyModel.get_by_id("test")
    assert check == expected


def test_find_or_spawn_corrupt_old_model_treated_as_create(
    ndb_context, monkeypatch, taskqueue_stub
) -> None:
    new_model = ManipulatorDummyModelWithRequiredProp(
        id="test", required_prop="new-value"
    )
    corrupt_old_model = ManipulatorDummyModelWithRequiredProp(id="test")

    monkeypatch.setattr(
        ndb,
        "get_multi",
        lambda *_args, **_kwargs: [corrupt_old_model],
    )

    result = DummyRequiredManipulator.createOrUpdate(new_model)

    assert result == new_model
    assert result._is_new is True
    assert result._dirty is False
    assert DummyRequiredManipulator.update_merge_calls == 0

    saved = ManipulatorDummyModelWithRequiredProp.get_by_id("test")
    assert saved is not None
    assert saved.required_prop == "new-value"


def test_update_model_leaves_unknown_attrs(ndb_context, taskqueue_stub) -> None:
    expected = ManipulatorDummyModel(
        id="test",
        int_prop=42,
    )
    expected.put()

    model = ManipulatorDummyModel.get_by_id("test")
    assert model is not None
    assert model == expected

    model.str_prop = "asdf"
    assert "str_prop" not in ManipulatorDummyModel._mutable_attrs

    DummyManipulator.createOrUpdate(model)
    check = ManipulatorDummyModel.get_by_id("test")
    assert check == expected


def test_does_not_assign_none(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=42)
    model.put()

    update = ManipulatorDummyModel(id="test", int_prop=None)
    DummyManipulator.createOrUpdate(update)

    check = ManipulatorDummyModel.get_by_id("test")
    assert check is not None
    assert check.int_prop == 42


def test_allow_none(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", can_be_none=42)
    model.put()

    update = ManipulatorDummyModel(id="test", can_be_none=None)
    DummyManipulator.createOrUpdate(update)

    check = ManipulatorDummyModel.get_by_id("test")
    assert check is not None
    assert check.int_prop is None


def test_stringified_none(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", mutable_str_prop="asdf")
    model.put()

    update = ManipulatorDummyModel(id="test", mutable_str_prop="None")
    DummyManipulator.createOrUpdate(update)

    check = ManipulatorDummyModel.get_by_id("test")
    assert check is not None
    assert check.mutable_str_prop is None


def test_update_lists(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", repeated_prop=[1, 2, 3])
    model.put()

    update = ManipulatorDummyModel(id="test", repeated_prop=[4, 5, 6])
    DummyManipulator.createOrUpdate(update)

    check = ManipulatorDummyModel.get_by_id("test")
    assert check is not None
    assert check.repeated_prop == [4, 5, 6]


def test_update_lists_empty_keeps_old(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", repeated_prop=[1, 2, 3])
    model.put()

    update = ManipulatorDummyModel(id="test", repeated_prop=[])
    DummyManipulator.createOrUpdate(update)

    check = ManipulatorDummyModel.get_by_id("test")
    assert check is not None
    assert check.repeated_prop == [1, 2, 3]


def test_update_json_attrs(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", prop_json=json.dumps({"foo": "bar"}))
    model.put()

    update = ManipulatorDummyModel(id="test", prop_json=json.dumps({"foo": "baz"}))
    DummyManipulator.createOrUpdate(update)

    check = ManipulatorDummyModel.get_by_id("test")
    assert check is not None
    assert check.prop_json == json.dumps({"foo": "baz"})
    assert check.prop == {"foo": "baz"}


def test_update_auto_union(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", union_prop=[1, 2, 3])
    model.put()

    update = ManipulatorDummyModel(id="test", union_prop=[4, 5, 6])
    DummyManipulator.createOrUpdate(update, auto_union=True)

    check = ManipulatorDummyModel.get_by_id("test")
    assert check is not None
    assert check.union_prop == [1, 2, 3, 4, 5, 6]


def test_update_auto_union_false(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", union_prop=[1, 2, 3])
    model.put()

    update = ManipulatorDummyModel(id="test", union_prop=[4, 5, 6])
    DummyManipulator.createOrUpdate(update, auto_union=False)

    check = ManipulatorDummyModel.get_by_id("test")
    assert check is not None
    assert check.union_prop == [4, 5, 6]


def test_update_auto_union_false_can_set_empty(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", union_prop=[1, 2, 3])
    model.put()

    update = ManipulatorDummyModel(id="test", union_prop=[])
    DummyManipulator.createOrUpdate(update, auto_union=False)

    check = ManipulatorDummyModel.get_by_id("test")
    assert check is not None
    assert check.union_prop == []


def test_cache_clearing(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=1337)
    model.put()

    # Do a query to populate CachedQueryResult
    query = DummyCachedQuery(model_key="test")
    query.fetch()

    assert CachedQueryResult.get_by_id(query.cache_key) is not None

    update = ManipulatorDummyModel(id="test", int_prop=42)
    DummyManipulator.createOrUpdate(update)

    # Ensure we've enqueued the cache clearing task to be run
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")
    assert len(tasks) == 1

    # This lets us ensure that the devserver can run our task
    # See https://github.com/GoogleCloudPlatform/appengine-python-standard/issues/45
    six.ensure_text(tasks[0].payload)

    # Run cache clearing manually
    run_from_task(tasks[0])

    # We should have cleared the cached result
    assert CachedQueryResult.get_by_id(query.cache_key) is None


def test_post_update_hook(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=1337)
    model.put()

    update = ManipulatorDummyModel(id="test", int_prop=42)
    DummyManipulator.createOrUpdate(update)

    # Ensure we've enqueued the hook to run
    assert DummyManipulator.update_calls == 0
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1

    # Run the hooks manually
    run_from_task(tasks[0])

    # Make sure the hook ran
    assert DummyManipulator.update_calls == 1


def test_update_hook_right_args(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=1337)
    model.put()

    update = ManipulatorDummyModel(id="test", int_prop=42)

    def update_hook_extra(models: List[TUpdatedModel[ManipulatorDummyModel]]) -> None:
        assert models == [
            TUpdatedModel(
                model=update,
                is_new=False,
                updated_attrs={"int_prop"},
            )
        ]

    DummyManipulator.update_hook_extra = update_hook_extra
    DummyManipulator.createOrUpdate(update)

    # Ensure we've enqueued the hook to run
    assert DummyManipulator.update_calls == 0
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1

    # Run the hooks manually
    run_from_task(tasks[0])

    # Make sure the hook ran
    assert DummyManipulator.update_calls == 1


def test_update_hook_creation(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=1337)

    def update_hook_extra(models: List[TUpdatedModel[ManipulatorDummyModel]]) -> None:
        assert models == [
            TUpdatedModel(
                model=model,
                is_new=True,
                updated_attrs=set(),
            )
        ]

    DummyManipulator.update_hook_extra = update_hook_extra
    DummyManipulator.createOrUpdate(model)

    # Ensure we've enqueued the hook to run
    assert DummyManipulator.update_calls == 0
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1

    # Run the hooks manually
    run_from_task(tasks[0])

    # Make sure the hook ran
    assert DummyManipulator.update_calls == 1


def test_update_skip_hook(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=1337)
    model.put()

    update = ManipulatorDummyModel(id="test", int_prop=42)
    DummyManipulator.createOrUpdate(update, run_post_update_hook=False)

    # Ensure we didn't enqueue the hook to run
    assert DummyManipulator.update_calls == 0
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 0


def test_delete_by_key(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=1337)
    model.put()

    DummyManipulator.delete_keys([model.key])

    assert ManipulatorDummyModel.get_by_id("test") is None


def test_delete_by_model(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=1337)
    model.put()

    DummyManipulator.delete([model])

    assert ManipulatorDummyModel.get_by_id("test") is None


def test_delete_clears_cache(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=1337)
    model.put()

    # Do a query to populate CachedQueryResult
    query = DummyCachedQuery(model_key="test")
    query.fetch()

    assert CachedQueryResult.get_by_id(query.cache_key) is not None
    DummyManipulator.delete([model])

    assert ManipulatorDummyModel.get_by_id("test") is None

    # Ensure we've enqueued the cache clearing task to be run
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")
    assert len(tasks) == 1

    # Run cache clearing manually
    run_from_task(tasks[0])

    # We should have cleared the cached result
    assert CachedQueryResult.get_by_id(query.cache_key) is None


def test_delete_runs_hook(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=1337)
    model.put()

    DummyManipulator.delete([model])

    # Ensure we've enqueued the hook to run
    assert DummyManipulator.delete_calls == 0
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1

    # Run the hooks manually
    run_from_task(tasks[0])

    # Make sure the hook ran
    assert DummyManipulator.delete_calls == 1


def test_delete_skip_hook(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=1337)
    model.put()

    DummyManipulator.delete([model], run_post_delete_hook=False)

    # Ensure we didn't enqueue the hook to run
    assert DummyManipulator.delete_calls == 0
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 0


def test_delete_hook_right_args(ndb_context, taskqueue_stub) -> None:
    model = ManipulatorDummyModel(id="test", int_prop=1337)
    model.put()

    def delete_hook_extra(models: List[ManipulatorDummyModel]) -> None:
        assert models == [model]

    DummyManipulator.delete_hook_extra = delete_hook_extra

    DummyManipulator.delete([model])

    # Ensure we've enqueued the hook to run
    assert DummyManipulator.delete_calls == 0
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="post-update-hooks")
    assert len(tasks) == 1

    # Run the hooks manually
    run_from_task(tasks[0])

    # Make sure the hook ran
    assert DummyManipulator.delete_calls == 1


def test_delete_hook_non_existent(ndb_context, taskqueue_stub) -> None:
    assert ManipulatorDummyModel.get_by_id("test") is None
    DummyManipulator.delete_keys([ndb.Key(ManipulatorDummyModel, "test")])

    # Ensure we didn't enqueue the hook to run
    tasks = taskqueue_stub.get_filtered_tasks(queue_names="cache-clearing")
    assert len(tasks) == 0


def test_merge_models() -> None:
    l1 = [ManipulatorDummyModel(id="k1", int_prop=42), ManipulatorDummyModel(id="k2")]
    l2 = [ManipulatorDummyModel(id="k1", int_prop=1337), ManipulatorDummyModel(id="k3")]

    merged = DummyManipulator.mergeModels(l1, l2)
    assert merged == [
        ManipulatorDummyModel(id="k1", int_prop=42),
        ManipulatorDummyModel(id="k2"),
        ManipulatorDummyModel(id="k3"),
    ]


def test_update_manual_attrs() -> None:
    old = ManipulatorDummyModel(id="test", int_prop=42, manual_attrs=["int_prop"])
    new = ManipulatorDummyModel(id="test", int_prop=604)

    merged = DummyManipulator.updateMerge(new, old, True, True)
    expected = ManipulatorDummyModel(id="test", int_prop=604, manual_attrs=["int_prop"])
    assert merged == expected


def test_no_update_manual_attrs() -> None:
    old = ManipulatorDummyModel(id="test", int_prop=42, manual_attrs=["int_prop"])
    new = ManipulatorDummyModel(id="test", int_prop=604)

    merged = DummyManipulator.updateMerge(new, old, True, False)
    expected = ManipulatorDummyModel(id="test", int_prop=42, manual_attrs=["int_prop"])
    assert merged == expected
