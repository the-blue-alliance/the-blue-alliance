import concurrent.futures
import time

from backend.common.cache.instance_cache import InstanceCache


def test_basic_get_set() -> None:
    cache: InstanceCache[str, str] = InstanceCache(ttl_seconds=10, max_size=5)
    assert cache.get("k1") is None
    cache.set("k1", "v1")
    assert cache.get("k1") == "v1"
    assert "k1" in cache
    assert len(cache) == 1


def test_delete() -> None:
    cache: InstanceCache[str, int] = InstanceCache(ttl_seconds=10, max_size=5)
    cache.set("k1", 100)
    assert cache.delete("k1") is True
    assert cache.get("k1") is None
    assert cache.delete("k1") is False
    assert len(cache) == 0


def test_clear() -> None:
    cache: InstanceCache[str, int] = InstanceCache(ttl_seconds=10, max_size=5)
    cache.set("a", 1)
    cache.set("b", 2)
    assert len(cache) == 2
    cache.clear()
    assert len(cache) == 0
    assert cache.get("a") is None
    assert cache.get("b") is None


def test_expiration() -> None:
    cache: InstanceCache[str, str] = InstanceCache(ttl_seconds=0.05, max_size=5)
    cache.set("fast", "val")
    assert cache.get("fast") == "val"
    time.sleep(0.06)
    assert cache.get("fast") is None
    assert "fast" not in cache
    assert len(cache) == 0


def test_custom_ttl_per_item() -> None:
    cache: InstanceCache[str, str] = InstanceCache(ttl_seconds=10.0, max_size=5)
    cache.set("short", "v1", ttl_seconds=0.05)
    cache.set("long", "v2", ttl_seconds=10.0)
    time.sleep(0.06)
    assert cache.get("short") is None
    assert cache.get("long") == "v2"


def test_lru_eviction() -> None:
    cache: InstanceCache[str, int] = InstanceCache(ttl_seconds=10, max_size=3)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)

    # Access 'a' so 'b' becomes the oldest
    assert cache.get("a") == 1

    # Adding 'd' should evict 'b'
    cache.set("d", 4)
    assert len(cache) == 3
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert cache.get("d") == 4


def test_concurrent_access_deadlock_free() -> None:
    cache: InstanceCache[int, str] = InstanceCache(ttl_seconds=5, max_size=50)

    def worker(worker_id: int) -> None:
        for i in range(100):
            key = (worker_id * 10 + i) % 100
            cache.set(key, f"val-{worker_id}-{i}")
            _ = cache.get(key)
            if i % 10 == 0:
                cache.delete(key)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker, i) for i in range(8)]
        for f in concurrent.futures.as_completed(futures):
            f.result()  # will raise if deadlock or exception occurred

    assert len(cache) <= 50
