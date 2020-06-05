import json

from backend.common.models.sitevar import Sitevar
from backend.common.sitevars.notifications_enable import NotificationsEnable


def test_default_sitevar():
    default_sitevar = NotificationsEnable._default_sitevar()
    assert default_sitevar is not None
    assert default_sitevar.contents is True


def test_notifications_enabled_insert():
    assert NotificationsEnable.notifications_enabled()


def test_notifications_enabled_get():
    Sitevar.get_or_insert("notifications.enable", values_json=json.dumps(False))
    assert not NotificationsEnable.notifications_enabled()


def test_enable_notifications():
    assert NotificationsEnable.notifications_enabled()
    NotificationsEnable.enable_notifications(False)
    assert not NotificationsEnable.notifications_enabled()
    NotificationsEnable.enable_notifications(True)
    assert NotificationsEnable.notifications_enabled()
