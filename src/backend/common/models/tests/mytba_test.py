import pytest

from backend.common.consts.model_type import ModelType
from backend.common.models.mytba import MyTBAModel


@pytest.mark.parametrize(
    "model_type, expected",
    [(ModelType.EVENT, True), (ModelType.TEAM, False), (ModelType.MATCH, False)],
)
def test_is_wildcard_type(model_type: ModelType, expected: bool) -> None:
    m = MyTBAModel(model_type=model_type, model_key="2020*")
    assert m.is_wildcard == expected


@pytest.mark.parametrize(
    "model_key, expected", [("2020miket", False), ("2020*", True), ("2020*mi", False)]
)
def test_is_wildcard(model_key: ModelType, expected: bool) -> None:
    m = MyTBAModel(model_type=ModelType.EVENT, model_key=model_key)
    assert m.is_wildcard == expected
