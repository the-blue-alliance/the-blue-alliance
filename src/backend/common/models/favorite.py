from datetime import datetime

from google.cloud import ndb
from pyre_extensions import safe_cast

from backend.common.consts.model_type import ModelType


class Favorite(ndb.Model):
    """
    In order to make strongly consistent DB requests, instances of this class
    should be created with a parent that is the associated Account key.
    """

    user_id: str = ndb.StringProperty(required=True)
    model_key: str = ndb.StringProperty(required=True)
    model_type: ModelType = safe_cast(
        ModelType, ndb.IntegerProperty(required=True, choices=list(ModelType))
    )

    created: datetime = ndb.DateTimeProperty(auto_now_add=True)
    updated: datetime = ndb.DateTimeProperty(auto_now=True)

    def __init__(self, *args, **kw):
        super(Favorite, self).__init__(*args, **kw)
