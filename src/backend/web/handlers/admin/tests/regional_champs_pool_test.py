import datetime
from unittest.mock import patch

from werkzeug.test import Client

from backend.common.models.regional_champs_pool import RegionalChampsPool


def test_regional_champs_pool_list_default_year(
    web_client: Client, login_gae_admin
) -> None:
    with patch("backend.web.handlers.admin.regional_champs_pool.datetime") as dt:
        dt.now.return_value = datetime.datetime(2025, 5, 1)
        resp = web_client.get("/admin/regional_champs_pool")
    assert resp.status_code == 200


def test_regional_champs_pool_list_with_pool(
    web_client: Client, login_gae_admin
) -> None:
    RegionalChampsPool(id=RegionalChampsPool.render_key_name(2025), year=2025).put()
    resp = web_client.get("/admin/regional_champs_pool/2025")
    assert resp.status_code == 200
