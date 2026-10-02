from unittest.mock import Mock, patch

from backend.tasks_io.datafeeds.datafeed_resource_library import (
    DatafeedResourceLibrary,
)

HTML = b"""
<html><body>
<details>
  <summary>2021 - Team 503, Frog Force - Novi, Michigan, USA</summary>
  <iframe src="https://www.youtube.com/embed/34gb_BMgnw8?si=abc"></iframe>
  <ul>
    <li><a href="https://www.firstinspires.org/essays/2021/503.pdf">503 Essay &amp; Executive Summaries</a></li>
    <li><a href="https://youtu.be/_o9urZ-pkxw">503 Chairman's Presentation</a></li>
  </ul>
</details>
</body></html>
"""


def test_get_hall_of_fame_teams() -> None:
    with patch(
        "requests.get", return_value=Mock(status_code=200, content=HTML)
    ) as mock_get:
        teams = DatafeedResourceLibrary().get_hall_of_fame_teams()

    mock_get.assert_called_once()
    assert mock_get.call_args[0][0] == DatafeedResourceLibrary.HALL_OF_FAME_URL

    assert teams == [
        {
            "team_id": "frc503",
            "team_number": 503,
            "year": 2021,
            "video": "34gb_BMgnw8",
            "presentation": "_o9urZ-pkxw",
            "essay": "https://www.firstinspires.org/essays/2021/503.pdf",
        }
    ]


def test_get_hall_of_fame_teams_fetch_failure() -> None:
    with patch("requests.get", return_value=Mock(status_code=500, content=b"")):
        teams = DatafeedResourceLibrary().get_hall_of_fame_teams()

    assert teams == []
