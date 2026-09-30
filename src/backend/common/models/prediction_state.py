from google.appengine.ext import ndb

from backend.common.models.cached_model import CachedModel


class SeasonPredictionState(CachedModel):
    """
    Metadata pointer for the SOTA predictor state of a season.
    Key: Season year as string (e.g., '2026').
    """

    season = ndb.IntegerProperty(required=True)
    model_version = ndb.StringProperty(required=True, default="hkf_ev_pcg_v1.0")
    last_updated = ndb.DateTimeProperty(auto_now=True)
    match_count = ndb.IntegerProperty(default=0)
    last_match_key = ndb.StringProperty()

    # GCS checkpoint storage pointer:
    # predictions/{season}/state_active.bin
    gcs_blob_path = ndb.StringProperty(required=True)
    state_hash = ndb.StringProperty()

    # Set of processed match keys stored as compressed JSON array for idempotency
    processed_match_keys_json = ndb.JsonProperty(compressed=True, default=list)


class SeasonPredictionCheckpoint(CachedModel):
    """
    Sub-second rewind checkpoints saved every 100 matches.
    Key: f"{season}_{match_step}"
    """

    season = ndb.IntegerProperty(required=True)
    match_step = ndb.IntegerProperty(required=True)
    last_match_key = ndb.StringProperty(required=True)
    timestamp = ndb.IntegerProperty(required=True)
    gcs_blob_path = ndb.StringProperty(required=True)
