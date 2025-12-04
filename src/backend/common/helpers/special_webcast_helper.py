from collections.abc import Generator
from typing import Any

from backend.common.futures import TypedFuture
from backend.common.memcache_models.webcast_online_status_memcache import (
    WebcastOnlineStatusMemcache,
)
from backend.common.models.webcast import Webcast
from backend.common.sitevars.gameday_special_webcasts import GamedaySpecialWebcasts
from backend.common.tasklets import typed_tasklet, typed_toplevel


class SpecialWebcastHelper:
    @classmethod
    @typed_toplevel
    def get_special_webcasts_with_online_status(
        cls,
    ) -> Generator[Any, Any, list[Webcast]]:
        webcasts = yield cls.get_special_webcasts_with_online_status_async()
        return webcasts

    @classmethod
    @typed_tasklet
    def get_special_webcasts_with_online_status_async(
        cls,
    ) -> Generator[Any, Any, list[Webcast]]:
        special_webcasts: list[Webcast] = []
        webcast_with_status_futures: list[TypedFuture[Webcast | None]] = []
        for webcast in GamedaySpecialWebcasts.webcasts():
            webcast_with_status_futures.append(
                WebcastOnlineStatusMemcache(webcast).get_async()
            )
            special_webcasts.append(webcast)

        webcasts_with_status: list[Webcast | None] = (yield webcast_with_status_futures)
        return [
            webcast_with_status if webcast_with_status is not None else webcast
            for webcast, webcast_with_status in zip(
                special_webcasts, webcasts_with_status
            )
        ]
