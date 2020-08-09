from typing import List, Optional, Set

from google.cloud import ndb

from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.cached_model import CachedModel


class DummyModel(CachedModel):
    int_prop: Optional[int] = ndb.IntegerProperty()
    str_prop: str = ndb.StringProperty()
    mutable_str_prop: str = ndb.StringProperty()
    can_be_none: Optional[int] = ndb.IntegerProperty()
    repeated_prop: List[int] = ndb.IntegerProperty(repeated=True)  # pyre-ignore[8]

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


class DummyManipulator(ManipulatorBase[DummyModel]):
    @classmethod
    def updateMerge(
        cls, new_model: DummyModel, old_model: DummyModel, auto_union: bool
    ) -> DummyModel:
        cls._update_attrs(new_model, old_model, auto_union)
        return old_model


def test_create_new_model(ndb_context) -> None:
    model = DummyModel(id="test", int_prop=42)
    put = DummyManipulator.createOrUpdate(model)
    assert put == model
    assert put._is_new is True

    check = DummyModel.get_by_id("test")
    assert check == model


def test_create_new_model_list(ndb_context) -> None:
    model1 = DummyModel(id="test1", int_prop=42)
    model2 = DummyModel(id="test2", int_prop=1337)
    put = DummyManipulator.createOrUpdate([model1, model2])
    assert put == [model1, model2]
    assert all(p._is_new for p in put)

    check1 = DummyModel.get_by_id("test1")
    check2 = DummyModel.get_by_id("test2")
    assert [check1, check2] == [model1, model2]


def test_update_model(ndb_context) -> None:
    model = DummyModel(id="test", int_prop=42)
    model.put()

    model.int_prop = 1337
    expected = DummyModel(id="test", int_prop=1337,)
    put = DummyManipulator.createOrUpdate(model)
    assert put == expected

    check = DummyModel.get_by_id("test")
    assert check == expected


def test_update_model_leaves_unknown_attrs(ndb_context) -> None:
    expected = DummyModel(id="test", int_prop=42,)
    expected.put()

    model = DummyModel.get_by_id("test")
    assert model == expected

    model.str_prop = "asdf"
    assert "str_prop" not in DummyModel._mutable_attrs

    DummyManipulator.createOrUpdate(model)
    check = DummyModel.get_by_id("test")
    assert check == expected


def test_does_not_assign_none(ndb_context) -> None:
    model = DummyModel(id="test", int_prop=42)
    model.put()

    update = DummyModel(id="test", int_prop=None)
    DummyManipulator.createOrUpdate(update)

    check = DummyModel.get_by_id("test")
    assert check.int_prop == 42


def test_allow_none(ndb_context) -> None:
    model = DummyModel(id="test", can_be_none=42)
    model.put()

    update = DummyModel(id="test", can_be_none=None)
    DummyManipulator.createOrUpdate(update)

    check = DummyModel.get_by_id("test")
    assert check.int_prop is None


def test_stringified_none(ndb_context) -> None:
    model = DummyModel(id="test", mutable_str_prop="asdf")
    model.put()

    update = DummyModel(id="test", mutable_str_prop="None")
    DummyManipulator.createOrUpdate(update)

    check = DummyModel.get_by_id("test")
    assert check.mutable_str_prop is None


def test_update_lists(ndb_context) -> None:
    model = DummyModel(id="test", repeated_prop=[1, 2, 3])
    model.put()

    update = DummyModel(id="test", repeated_prop=[4, 5, 6])
    DummyManipulator.createOrUpdate(update)

    check = DummyModel.get_by_id("test")
    assert check.repeated_prop == [4, 5, 6]


def test_update_lists_empty_keeps_old(ndb_context) -> None:
    model = DummyModel(id="test", repeated_prop=[1, 2, 3])
    model.put()

    update = DummyModel(id="test", repeated_prop=[])
    DummyManipulator.createOrUpdate(update)

    check = DummyModel.get_by_id("test")
    assert check.repeated_prop == [1, 2, 3]
