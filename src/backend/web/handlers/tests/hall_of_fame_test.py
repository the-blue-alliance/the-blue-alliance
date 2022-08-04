from werkzeug.test import Client

from backend.web.handlers.tests import helpers


def test_hof_page_loads(web_client: Client) -> None:
    resp = web_client.get("/hall-of-fame")
    assert resp.status_code == 200


def test_2022_hof_info(web_client: Client, setup_hof_awards) -> None:
    setup_hof_awards("2021cmpaw", ["frc503", "frc4613"])
    setup_hof_awards("2022cmptx", ["frc1629"])

    resp = web_client.get("/hall-of-fame")

    assert resp.status_code == 200
    assert helpers.get_page_title(resp.data) == "FIRST Hall of Fame - The Blue Alliance"

    hof_awards = helpers.get_HOF_awards(resp.data)
    assert hof_awards == [
        helpers.TeamHOFInfo(
            team_number=1629, year="2022", event="2022 Houston Championship"
        ),
        helpers.TeamHOFInfo(
            team_number=503, year="2021", event="2021 Manchester Championship"
        ),
        helpers.TeamHOFInfo(
            team_number=4613, year="2021", event="2021 Manchester Championship"
        ),
    ]
