from werkzeug.test import Client

from backend.web.handlers.tests import helpers


def test_hof_page_loads(web_client: Client) -> None:
    resp = web_client.get("/hall-of-fame")
    assert resp.status_code == 200


def test_2022_hof_info(web_client: Client, setup_hof_awards) -> None:
    # helpers.import_team()
    setup_hof_awards("2021cmpaw", ["frc503", "frc4613"])
    setup_hof_awards("2022cmptx", ["frc1629"])

    resp = web_client.get("/hall-of-fame")
    assert resp.status_code == 200

    # print(resp.data)

    assert helpers.get_page_title(resp.data) == "FIRST Hall of Fame - The Blue Alliance"

    hof_awards = helpers.get_HOF_awards(resp.data)

    print(hof_awards)

    # assert team_history == [
    #     helpers.TeamEventHistory(year=2019, event="The Remix", awards=[]),
    #     helpers.TeamEventHistory(
    #         year=2019, event="Texas Robotics Invitational", awards=[]
    #     ),
    #     helpers.TeamEventHistory(
    #         year=2019, event="Einstein Field (Houston)", awards=[]
    #     ),
    #     helpers.TeamEventHistory(
    #         year=2019,
    #         event="Roebling Division",
    #         awards=[
    #             "Championship Subdivision Winner",
    #             "Quality Award sponsored by Motorola Solutions Foundation",
    #         ],
    #     ),
    #     helpers.TeamEventHistory(
    #         year=2019,
    #         event="FIRST In Texas District Championship",
    #         awards=["District Championship Winner"],
    #     ),
    #     helpers.TeamEventHistory(
    #         year=2019,
    #         event="FIT District Dallas Event",
    #         awards=[
    #             "District Event Winner",
    #             "Industrial Design Award sponsored by General Motors",
    #         ],
    #     ),
    #     helpers.TeamEventHistory(
    #         year=2019,
    #         event="FIT District Amarillo Event",
    #         awards=[
    #             "District Event Winner",
    #             "Quality Award sponsored by Motorola Solutions Foundation",
    #         ],
    #     ),
    # ]
