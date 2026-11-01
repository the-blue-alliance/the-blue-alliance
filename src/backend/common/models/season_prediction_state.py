from typing import Dict

from google.appengine.ext import ndb

from backend.common.models.keys import Year


class SeasonPredictionState(ndb.Model):
    """
    Pointer to one season's predictions_v2 model state in Cloud Storage.
    key_name is the season, like '2024'

    The state, match log and checkpoints are double-buffered blobs: a write goes to
    the slot that this entity does not point at, then the entity is updated. Only the
    predictions_v2 pipeline writes it (see helpers/predictions_v2/store.py). It is
    never served, so it is not a CachedModel.
    """

    season: Year = ndb.IntegerProperty(required=True)
    # Model version and configuration that wrote the state.
    model_fingerprint = ndb.StringProperty(required=True)
    # Incremented on every save; the state and log are in slot generation % 2.
    generation = ndb.IntegerProperty(required=True)
    log_length = ndb.IntegerProperty(required=True)
    # Log index -> slot of the checkpoint taken before that log entry.
    checkpoints: Dict[str, int] = ndb.JsonProperty(default={})

    updated = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def key_for(cls, season: Year) -> ndb.Key:
        return ndb.Key(cls, str(season))
