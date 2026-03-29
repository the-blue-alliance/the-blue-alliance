from datetime import datetime
from typing import cast, Dict, List, Optional

from google.appengine.ext import ndb

from backend.common.models.account import Account


class AuditLogEntry(ndb.Model):
    time: datetime = ndb.DateTimeProperty(auto_now_add=True)
    account = ndb.KeyProperty(kind=Account)
    endpoint: str = ndb.StringProperty(required=True)
    target_key: Optional[ndb.Key] = ndb.KeyProperty()
    url_args: Dict[str, str] = cast(Dict[str, str], ndb.JsonProperty(indexed=False))
    form_params: Dict[str, List[str]] = cast(
        Dict[str, List[str]], ndb.JsonProperty(indexed=False)
    )
