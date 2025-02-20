from backend.common.consts.webcast_type import WebcastType
from backend.common.sitevars.gameday_special_webcasts import (
    GamedaySpecialWebcasts,
    WebcastType as TSpecialWebcast,
)


def test_get_default() -> None:
    default_sitevar = GamedaySpecialWebcasts.get()
    assert default_sitevar == {
        "default_chat": "tbagameday",
        "webcasts": [],
        "aliases": {},
    }


def test_add_special_webcast() -> None:
    webcast = TSpecialWebcast(
        type=WebcastType.TWITCH,
        channel="tbagameday",
        name="TBA Gameday",
        key_name="tbagameday",
    )
    GamedaySpecialWebcasts.add_special_webcast(webcast)

    special_webcasts = GamedaySpecialWebcasts.webcasts()
    assert special_webcasts == [webcast]


def test_add_special_webcast_duplicate() -> None:
    webcast = TSpecialWebcast(
        type=WebcastType.TWITCH,
        channel="tbagameday",
        name="TBA Gameday",
        key_name="tbagameday",
    )
    GamedaySpecialWebcasts.add_special_webcast(webcast)
    GamedaySpecialWebcasts.add_special_webcast(webcast)

    special_webcasts = GamedaySpecialWebcasts.webcasts()
    assert special_webcasts == [webcast]


def test_remove_special_webcast() -> None:
    webcast = TSpecialWebcast(
        type=WebcastType.TWITCH,
        channel="tbagameday",
        name="TBA Gameday",
        key_name="tbagameday",
    )

    initial_value = GamedaySpecialWebcasts.default_value()
    initial_value["webcasts"] = [webcast]
    GamedaySpecialWebcasts.put(initial_value)

    GamedaySpecialWebcasts.remove_special_webcast("tbagameday")

    special_webcasts = GamedaySpecialWebcasts.webcasts()
    assert special_webcasts == []


def test_remove_special_webcast_from_empty() -> None:
    initial_value = GamedaySpecialWebcasts.default_value()
    initial_value["webcasts"] = []
    GamedaySpecialWebcasts.put(initial_value)

    GamedaySpecialWebcasts.remove_special_webcast("tbagameday")

    special_webcasts = GamedaySpecialWebcasts.webcasts()
    assert special_webcasts == []


def test_remove_special_webcast_doesnt_exist() -> None:
    webcast = TSpecialWebcast(
        type=WebcastType.TWITCH,
        channel="tbagameday",
        name="TBA Gameday",
        key_name="tbagameday",
    )

    initial_value = GamedaySpecialWebcasts.default_value()
    initial_value["webcasts"] = [webcast]
    GamedaySpecialWebcasts.put(initial_value)

    GamedaySpecialWebcasts.remove_special_webcast("tbagameday2")

    special_webcasts = GamedaySpecialWebcasts.webcasts()
    assert special_webcasts == [webcast]


def test_add_alias() -> None:
    GamedaySpecialWebcasts.add_alias("cmp", "tbagameday")

    assert GamedaySpecialWebcasts.get_alias("cmp") == "tbagameday"


def test_add_alias_overwrite() -> None:
    initial_value = GamedaySpecialWebcasts.default_value()
    initial_value["aliases"] = {"cmp": "asdf"}
    GamedaySpecialWebcasts.put(initial_value)

    GamedaySpecialWebcasts.add_alias("cmp", "tbagameday")

    assert GamedaySpecialWebcasts.get_alias("cmp") == "tbagameday"


def test_remove_alias() -> None:
    initial_value = GamedaySpecialWebcasts.default_value()
    initial_value["aliases"] = {"cmp": "asdf"}
    GamedaySpecialWebcasts.put(initial_value)

    GamedaySpecialWebcasts.remove_alias("cmp")

    assert GamedaySpecialWebcasts.get_alias("cmp") is None


def test_remove_alias_doesnt_exist() -> None:
    initial_value = GamedaySpecialWebcasts.default_value()
    initial_value["aliases"] = {"cmp": "asdf"}
    GamedaySpecialWebcasts.put(initial_value)

    GamedaySpecialWebcasts.remove_alias("adsf")

    assert GamedaySpecialWebcasts.get_alias("cmp") == "asdf"


def test_set_default_chat() -> None:
    GamedaySpecialWebcasts.set_default_chat("tbagameday2")
    assert GamedaySpecialWebcasts.default_chat() == "tbagameday2"
