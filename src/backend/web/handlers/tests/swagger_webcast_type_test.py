import json
from pathlib import Path
from typing import Any, Iterator


from backend.common.consts.webcast_type import WebcastType

SWAGGER_DIR = Path(__file__).resolve().parents[2] / "static" / "swagger"


def _webcast_type_enums(node: Any) -> Iterator[list[str]]:
    if isinstance(node, dict):
        enum = node.get("enum")
        if isinstance(enum, list) and WebcastType.TWITCH.value in enum:
            yield enum
        for value in node.values():
            yield from _webcast_type_enums(value)
    elif isinstance(node, list):
        for value in node:
            yield from _webcast_type_enums(value)


def _spec(name: str) -> Any:
    return json.loads((SWAGGER_DIR / name).read_text())


def test_trusted_webcast_type_enums_match_server() -> None:
    enums = list(_webcast_type_enums(_spec("api_trusted_v1.json")))

    assert enums
    for enum in enums:
        assert sorted(enum) == sorted(t.value for t in WebcastType)


def test_read_webcast_type_enums_include_server_types() -> None:
    # The read API also returns legacy types (e.g. "justin") from old events.
    enums = list(_webcast_type_enums(_spec("api_v3.json")))

    assert enums
    for enum in enums:
        assert {t.value for t in WebcastType} <= set(enum)
