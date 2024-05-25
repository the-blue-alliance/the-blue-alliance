from unittest.mock import Mock, patch

from requests_mock import ANY, Mocker

from backend.common.environment.environment import Environment
from backend.common.helpers.outgoing_notification_helper import (
    OutgoingNotificationHelper,
)


URL = "https://foo.bar.com/"


def test_skip_if_nonprod(requests_mock: Mocker) -> None:
    requests_mock.post(ANY, exc=Exception)

    OutgoingNotificationHelper.send_slack_alert(URL, "text")


@patch.object(Environment, "is_prod")
def test_send_notification(env_mock: Mock, requests_mock: Mocker) -> None:
    env_mock.return_value = True
    requests_mock.post(URL, text="success")

    OutgoingNotificationHelper.send_slack_alert(URL, "test!")


@patch.object(Environment, "is_prod")
def test_send_notification_with_attachment(
    env_mock: Mock, requests_mock: Mocker
) -> None:
    env_mock.return_value = True
    requests_mock.post(URL, text="success")

    OutgoingNotificationHelper.send_slack_alert(URL, "test!", attachment_list=["foo"])
