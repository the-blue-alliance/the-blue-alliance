import inspect

from backend.web.profiled_render import render_template


def cached_query_list() -> str:
    from backend.common import queries
    print(inspect.getmembers(queries, inspect.isclass))
    return ""
