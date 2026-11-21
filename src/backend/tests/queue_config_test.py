from typing import Any, Dict

import yaml

QUEUE_YAML = "src/queue.yaml"


def _queue(name: str) -> Dict[str, Any]:
    with open(QUEUE_YAML) as f:
        queues = yaml.safe_load(f)["queue"]
    return next(q for q in queues if q["name"] == name)


def test_cache_clearing_retries_are_bounded() -> None:
    retry = _queue("cache-clearing").get("retry_parameters", {})
    assert 0 < retry.get("task_retry_limit", -1) <= 10
