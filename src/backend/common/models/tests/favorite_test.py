from backend.common.consts.model_type import ModelType
from backend.common.models.favorite import Favorite


def test_to_json() -> None:
    favorite = Favorite(
        model_type=ModelType.TEAM,
        model_key="frc254",
    )
    assert favorite.to_json() == {
        "model_type": 1,
        "model_key": "frc254",
    }
