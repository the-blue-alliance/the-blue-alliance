from datetime import timedelta

from backend.common.memcache_models.memcache_model import MemcacheModel
from backend.common.models.webcast import Webcast


class WebcastOnlineStatusMemcache(MemcacheModel[Webcast]):

    def __init__(self, webcast: Webcast) -> None:
        super().__init__()
        self.type = webcast["type"]
        self.channel = webcast.get("channel")
        self.file = webcast.get("file")

    def key(self) -> bytes:
        return f"webcast_status:{self.type}:{self.channel}:{self.file}".encode()

    def ttl(self) -> timedelta:
        return timedelta(minutes=5)
