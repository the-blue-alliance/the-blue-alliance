from google.cloud import ndb
from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.sitevar import Sitevar


def test_no_status(ndb_client: ndb.Client, api_client: Client) -> None:
    with ndb_client.context():
        ApiAuthAccess(
            id="test_auth_key",
            auth_types_enum=[AuthType.READ_API],
        ).put()
    resp = api_client.get("/api/v3/status", headers={"X-TBA-Auth-Key": "test_auth_key"})
    assert resp.status_code == 404


def test_status(ndb_client: ndb.Client, api_client: Client) -> None:
    with ndb_client.context():
        ApiAuthAccess(
            id="test_auth_key",
            auth_types_enum=[AuthType.READ_API],
        ).put()
        sitevar = Sitevar(id="apistatus")
        sitevar.contents = {"test": 5}
        sitevar.put()
    resp = api_client.get("/api/v3/status", headers={"X-TBA-Auth-Key": "test_auth_key"})
    assert resp.status_code == 200
    assert resp.json["test"] == 5
