from unittest.mock import Mock, patch

import pytest

from requests_mock import ANY, Mocker

import backend.common.helpers.outgoing_notification_helper as helper_module
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


def _prod(monkeypatch: pytest.MonkeyPatch, project: str = "tbatv-prod-hrd") -> None:
    monkeypatch.setenv("GAE_ENV", "standard")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", project)


def test_email_disabled_outside_app_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GAE_ENV", raising=False)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "tbatv-prod-hrd")
    assert not OutgoingNotificationHelper.email_enabled()


def test_email_disabled_on_other_projects(monkeypatch: pytest.MonkeyPatch) -> None:
    # A contributor's own GAE deploy must never email real requesters
    _prod(monkeypatch, project="tbatv-dev-someone")
    assert not OutgoingNotificationHelper.email_enabled()


def test_email_enabled_in_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    _prod(monkeypatch)
    assert OutgoingNotificationHelper.email_enabled()


def test_admin_alert_email_skipped_when_disabled() -> None:
    with patch.object(helper_module.mail, "send_mail") as send_mail:
        OutgoingNotificationHelper.send_admin_alert_email("Subject", "Body")
        OutgoingNotificationHelper.send_suggestion_result_email(
            "someone@example.com", "Subject", "Body"
        )
    send_mail.assert_not_called()


def test_admin_alert_email_in_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    _prod(monkeypatch)
    with patch.object(helper_module.mail, "send_mail") as send_mail:
        OutgoingNotificationHelper.send_admin_alert_email("Subject", "Body")

    send_mail.assert_called_once_with(
        sender="The Blue Alliance Contact <contact@thebluealliance.com>",
        to="contact@thebluealliance.com",
        subject="Subject",
        body="Body",
    )


def test_suggestion_result_email_in_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    _prod(monkeypatch)
    with patch.object(helper_module.mail, "send_mail") as send_mail:
        OutgoingNotificationHelper.send_suggestion_result_email(
            "someone@example.com", "Subject", "Body"
        )

    # contact@ is cc'd so the admins keep a record of what was sent
    send_mail.assert_called_once_with(
        sender="The Blue Alliance Admin <contact@thebluealliance.com>",
        to="someone@example.com",
        cc="contact@thebluealliance.com",
        subject="Subject",
        body="Body",
    )


def test_send_failure_propagates_so_the_task_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prod(monkeypatch)
    with patch.object(
        helper_module.mail, "send_mail", side_effect=RuntimeError("mail down")
    ):
        with pytest.raises(RuntimeError):
            OutgoingNotificationHelper.send_admin_alert_email("Subject", "Body")
