from typing_extensions import TypedDict

from backend.common.consts.model_type import ModelType
from backend.common.models.mytba import MyTBAModel


class FavoriteDict(TypedDict):
    model_type: ModelType
    model_key: str


class Favorite(MyTBAModel):
    """
    In order to make strongly consistent DB requests, instances of this class
    should be created with a parent that is the associated Account key.
    """

    def __init__(self, *args, **kwargs):
        super(Favorite, self).__init__(*args, **kwargs)

    def to_json(self) -> FavoriteDict:
        return {
            "model_type": self.model_type,
            "model_key": self.model_key,
        }
