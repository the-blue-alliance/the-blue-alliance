"""Every URL in cron.yaml must resolve to a route on the service that serves it.

Three cron entries (`/backend-tasks/backup/enqueue`,
`/tasks/enqueue/update_all_team_search_index`, `/tasks/get/hof_teams`) survived the
Python 2 -> 3 migration without their handlers and returned 404 on every run for
roughly four years. Nothing alerted, because nothing checks. This does.
"""

import fnmatch
from typing import Dict, List, Optional

import pytest
import yaml
from werkzeug.exceptions import MethodNotAllowed
from werkzeug.routing import Map

CRON_YAML = "src/cron.yaml"
DISPATCH_YAML = "src/dispatch.yaml"

# Service name -> module path of the Flask app that serves it.
SERVICE_MODULES = {
    "py3-web": "backend.web.main",
    "py3-api": "backend.api.main",
    "py3-tasks-io": "backend.tasks_io.main",
    "py3-tasks-cpu": "backend.tasks_cpu.main",
    "py3-tasks-cpu-enqueue": "backend.tasks_cpu.main",
}


def _dispatch_rules() -> List[Dict[str, str]]:
    with open(DISPATCH_YAML) as f:
        return yaml.safe_load(f)["dispatch"]


def _cron_entries() -> List[Dict[str, str]]:
    with open(CRON_YAML) as f:
        return yaml.safe_load(f)["cron"]


def _service_for(path: str, rules: List[Dict[str, str]]) -> str:
    """Resolve a path to a service the way App Engine's dispatch does.

    Cron requests arrive on the app's default hostname, so host-specific rules
    (e.g. `beta.thebluealliance.com/*`) never apply to them.
    """
    for rule in rules:
        host, _, pattern = rule["url"].partition("/")
        if host not in ("*", ""):
            continue
        if fnmatch.fnmatch(path.lstrip("/"), pattern.lstrip("/")):
            return rule["service"]
    return "py3-web"


def _url_map(service: str) -> Optional[Map]:
    module_path = SERVICE_MODULES.get(service)
    if module_path is None:
        return None
    module = __import__(module_path, fromlist=["app"])
    return module.app.url_map


def _resolves(path: str, url_map: Map) -> bool:
    adapter = url_map.bind("localhost")
    try:
        adapter.match(path, method="GET")
        return True
    except MethodNotAllowed:
        # The route exists, it just does not accept GET. App Engine cron issues
        # GET, but a POST-only handler is a separate concern from a missing one.
        return True
    except Exception:
        return False


@pytest.mark.parametrize("entry", _cron_entries(), ids=lambda e: e["url"])
def test_cron_url_resolves_to_a_real_route(entry: Dict[str, str]) -> None:
    path = entry["url"].split("?")[0]
    service = _service_for(path, _dispatch_rules())

    url_map = _url_map(service)
    assert url_map is not None, (
        f"cron entry {path!r} dispatches to unknown service {service!r}; "
        f"add it to SERVICE_MODULES or fix dispatch.yaml"
    )

    assert _resolves(path, url_map), (
        f"cron entry {path!r} dispatches to {service} but no route matches it. "
        f"It will 404 on every run ({entry.get('schedule')}). Either remove the "
        f"cron entry or add the handler."
    )
