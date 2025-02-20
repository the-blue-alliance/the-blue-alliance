from datetime import datetime
from typing import cast

from google.appengine.ext import ndb

from backend.common.consts.model_type import ModelType


class MyTBAModel(ndb.Model):
    user_id: str = ndb.StringProperty(required=True)
    model_key: str = ndb.StringProperty(required=True)
    model_type: ModelType = cast(
        ModelType, ndb.IntegerProperty(required=True, choices=list(ModelType))
    )

    created: datetime = ndb.DateTimeProperty(auto_now_add=True)
    updated: datetime = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kwargs):
        super(MyTBAModel, self).__init__(*args, **kwargs)

    @property
    def is_wildcard(self) -> bool:
        # myTBA Event models ending in * are "all events for year" wildcards (used for webhooks primarily)
        if not self.model_type == ModelType.EVENT:
            return False
        return self.model_key.endswith("*")
