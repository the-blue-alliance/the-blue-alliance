from typing import Set

from google.cloud import ndb

from backend.common.manipulators.manipulator_base import ManipulatorBase
from backend.common.models.cached_model import CachedModel


class DummyModel(CachedModel):
    int_prop: int = ndb.IntegerProperty()
    str_prop: str = ndb.StringProperty()

    _mutable_attrs: Set[str] = {
        "int_prop",
    }


class DummyManipulator(ManipulatorBase[DummyModel]):
    @classmethod
    def updateMerge(
        cls, new_model: DummyModel, old_model: DummyModel, auto_union: bool
    ) -> DummyModel:
        cls._update_attrs(new_model, old_model, DummyModel._mutable_attrs)
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
