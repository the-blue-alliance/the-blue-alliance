from backend.common.sitevars.notifications_enable import NotificationsEnable


def test_key():
    assert NotificationsEnable.key() == "notifications.enable"


def test_description():
    assert (
        NotificationsEnable.description() == "For enabling/disabling all notifications"
    )


def test_default_sitevar():
    default_sitevar = NotificationsEnable._fetch_sitevar()
    assert default_sitevar is not None
    assert default_sitevar.contents is True
    assert default_sitevar.description == "For enabling/disabling all notifications"


def test_notifications_enabled_insert():
    assert NotificationsEnable.notifications_enabled()


def test_notifications_enabled_get():
    NotificationsEnable.put(False)
    assert not NotificationsEnable.notifications_enabled()


def test_enable_notifications():
    assert NotificationsEnable.notifications_enabled()
    NotificationsEnable.enable_notifications(False)
    assert not NotificationsEnable.notifications_enabled()
    NotificationsEnable.enable_notifications(True)
    assert NotificationsEnable.notifications_enabled()
