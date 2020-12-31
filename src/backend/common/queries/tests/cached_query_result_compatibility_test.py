import base64
import datetime

from google.cloud import ndb

from backend.common.models.cached_query_result import CachedQueryResult
from backend.common.models.media import Media

"""
The purpose of these tests is to make sure that py3 can deserialize cached query results
pickled by the py2 version of the site.

We do a bit of ndb hackery to test it. We start with a base64 encoded cached query, pulled
from the datastore admin tool on prod. We then construct a dummy model (as the value of the
property has already been pickled+compressed for storage) and then round-trip it to a datastore
Entity, to force the ndb library to interpret the raw data as a different model type. This will
let us prove we can deserialize it.

If we do nothing, this fails because the import path of models has changed between py2/py3.
It would fail with a message like:

E       ModuleNotFoundError: No module named 'models'
"""


class RawCachedQueryResult(ndb.Model):
    result = ndb.Property()

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def _get_kind(cls):
        return "CachedQueryResult"


def test_cached_result_team_social_media() -> None:

    raw_model = RawCachedQueryResult(
        id="py2_data",
        # This is a py2 serialized value, pulled from the datastore admin tool
        result=base64.b64decode(
            "eJyVkLFKxEAURZO4kphdUMKCMtUiKriwK4iI1tZ228owm3mJEzOT5M1kISlE7fQL/AELCz/JT7C1NjuITSqbV9x7OFzeg3dTubEsOOR6LoELFl7bW3nHj9XGgrqOk11lO/reLJlZzUos+OwWOZ4Mo01L7h8IpQ1Lkcl1m4gcqBGGKVFLI1JAfXZxejnCQzJMCgSRKnoHzcSZjknU53CXbNsZ1DQlUFC17FAv8PGchAgJIKgY9MSdHsX9VbodLIDJF9dPMF7rDMeQDBpg2Fmcdi/wiR8jMAO8C7aC1+/n94/PL6+NyIiDYSLXNNOFsjQh4xLFqoNpr7OmuuR/prdf05P7388s2fwH/A+AHg=="
        ),
    )
    raw_entity = ndb.model._entity_to_ds_entity(raw_model)  # pyre-ignore

    query_result = ndb.model._entity_from_ds_entity(  # pyre-ignore
        raw_entity, model_class=CachedQueryResult
    )

    assert query_result.result == [
        Media(
            created=datetime.datetime(2020, 12, 20, 20, 3, 17, 962520),
            details_json=None,
            foreign_key="titaniumtigers4829",
            media_type_enum=7,
            private_details_json=None,
            references=[
                ndb.Key("Team", "frc4829", project="tbatv-prod-hrd", namespace="")
            ],
            updated=datetime.datetime(2020, 12, 20, 20, 3, 17, 962533),
            year=None,
        )
    ]
