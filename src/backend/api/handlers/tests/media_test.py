from werkzeug.test import Client

from backend.common.consts.auth_type import AuthType
from backend.common.consts.media_tag import TAG_NAMES, TAG_URL_NAMES
from backend.common.models.api_auth_access import ApiAuthAccess


def test_media_tags(ndb_stub, api_client: Client) -> None:
    ApiAuthAccess(
        id="test_auth_key",
        auth_types_enum=[AuthType.READ_API],
    ).put()

    resp = api_client.get(
        "/api/v3/media/tags", headers={"X-TBA-Auth-Key": "test_auth_key"}
    )
    assert resp.status_code == 200
    assert len(resp.json) == len(TAG_NAMES)
    for tag in resp.json:
        assert tag["name"] in TAG_NAMES.values()
        assert tag["code"] in TAG_URL_NAMES.values()
