import bs4
from werkzeug.test import Client

from backend.web.handlers.tests import helpers


def test_team_detail_has_audit_logs_link(web_client: Client, login_gae_admin) -> None:
    helpers.preseed_team(1124)

    resp = web_client.get("/admin/team/1124")
    assert resp.status_code == 200

    soup = bs4.BeautifulSoup(resp.data, "html.parser")
    audit_logs_link = soup.find("a", href="/admin/audit_logs?key=Team:frc1124")
    assert audit_logs_link is not None
