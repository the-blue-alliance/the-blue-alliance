"""
Guards against https://github.com/the-blue-alliance/the-blue-alliance/issues/10495.

`cached_public` keys its cache on path + query string only, with no user
component, so the rendered HTML body is stored once and served to every
visitor. A CSRF token is per-session, so rendering `csrf_token()` into a
publicly cached page hands whichever token warmed the cache to everyone else,
and their POSTs are rejected with a 400.

This test walks every web handler decorated with `cached_public`, resolves the
templates it renders (transitively through extends/include/import, and through
dynamic includes by globbing the format strings that build their names), and
asserts none of them reference `csrf_token`. Client-side code that needs a
token should fetch one from `/_/account/info` instead.
"""

import ast
import re
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

import pytest
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from jinja2 import meta as jinja_meta

WEB_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = WEB_ROOT.parent.parent
HANDLERS_ROOT = WEB_ROOT / "handlers"
TEMPLATES_ROOT = WEB_ROOT / "templates"

CSRF_TOKEN_RE = re.compile(r"\bcsrf_token\s*\(")

# A quoted string ending in .html, e.g. "event_partials/event_insights_{}.html"
QUOTED_TEMPLATE_NAME_RE = re.compile(r"""["']([^"'\n]*\.html)["']""")
FORMAT_PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}")

_jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_ROOT)))


class RenderedTemplate(NamedTuple):
    module: str
    handler: str
    template: str


def _decorator_name(node: ast.expr) -> str | None:
    # Handles @cached_public, @cached_public(ttl=...), and @module.cached_public
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _called_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _module_functions(tree: ast.Module) -> dict[str, ast.AST]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _render_calls(
    func: ast.AST, module_functions: dict[str, ast.AST]
) -> list[ast.Call]:
    """`render_template` calls in `func` and in the helpers it delegates to.

    A handler doesn't have to render inline: `index` picks one of six
    `index_*` helpers out of a dict and returns its result, so walking only the
    decorated function would miss every template those helpers render. Follow
    any reference to a module-level function, not just direct calls, since
    helpers are often passed around as values before being invoked.
    """
    calls: list[ast.Call] = []
    visited: set[int] = set()
    pending = [func]
    while pending:
        current = pending.pop()
        if id(current) in visited:
            continue
        visited.add(id(current))
        for node in ast.walk(current):
            if isinstance(node, ast.Call) and _called_name(node) == "render_template":
                calls.append(node)
            elif isinstance(node, ast.Name) and node.id in module_functions:
                pending.append(module_functions[node.id])
    return calls


def _cached_public_renders() -> Iterator[RenderedTemplate]:
    for path in sorted(HANDLERS_ROOT.rglob("*.py")):
        if "tests" in path.parts:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        module = str(path.relative_to(SRC_ROOT))
        module_functions = _module_functions(tree)
        for func in ast.walk(tree):
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not any(
                _decorator_name(d) == "cached_public" for d in func.decorator_list
            ):
                continue
            for call in _render_calls(func, module_functions):
                if not call.args:
                    continue
                name = call.args[0]
                # Dynamically-named templates can't be resolved statically.
                # There are none today; fail loudly if one is introduced so
                # this test doesn't silently stop covering a handler.
                assert isinstance(name, ast.Constant) and isinstance(
                    name.value, str
                ), f"{module}:{call.lineno} renders a non-literal template name"
                yield RenderedTemplate(module, func.name, name.value)


def _template_source(template: str) -> str:
    try:
        source, _, _ = _jinja_env.loader.get_source(_jinja_env, template)  # pyre-ignore
    except TemplateNotFound:
        raise AssertionError(f"Template {template} not found under {TEMPLATES_ROOT}")
    return source


def _referenced_templates(template: str, seen: set[str]) -> set[str]:
    """All templates reachable from `template` via extends/include/import."""
    if template in seen:
        return seen
    seen.add(template)
    parsed = _jinja_env.parse(_template_source(template))
    for referenced in jinja_meta.find_referenced_templates(parsed):
        if referenced is None:
            # A dynamic `{% include some_var %}`; resolved by the caller.
            continue
        _referenced_templates(referenced, seen)
    return seen


def _has_dynamic_reference(template: str) -> bool:
    parsed = _jinja_env.parse(_template_source(template))
    return any(ref is None for ref in jinja_meta.find_referenced_templates(parsed))


def _template_name_patterns(source: str) -> set[str]:
    """Globs for template names built at runtime from a format string.

    `"event_partials/event_insights_{}.html".format(year)` in a handler or a
    template yields `event_partials/event_insights_*.html`.
    """
    return {
        FORMAT_PLACEHOLDER_RE.sub("*", name)
        for name in QUOTED_TEMPLATE_NAME_RE.findall(source)
        if "{" in name
    }


def _glob_templates(patterns: set[str]) -> set[str]:
    return {
        path.relative_to(TEMPLATES_ROOT).as_posix()
        for pattern in patterns
        for path in TEMPLATES_ROOT.glob(pattern)
        if path.is_file()
    }


def _reachable_templates(render: RenderedTemplate) -> set[str]:
    """Every template `render` can pull in, including dynamic includes."""
    reachable = _referenced_templates(render.template, set())

    dynamic = sorted(t for t in reachable if _has_dynamic_reference(t))
    if not dynamic:
        return reachable

    # `{% include some_var %}` can't be followed statically, but the values are
    # always built from a format string in the rendering handler or in one of
    # the templates it reaches. Glob those patterns and scan every template
    # they could resolve to, so a year-specific partial can't reintroduce a
    # cached csrf_token unnoticed.
    patterns = _template_name_patterns((SRC_ROOT / render.module).read_text())
    for template in sorted(reachable):
        patterns |= _template_name_patterns(_template_source(template))
    candidates = _glob_templates(patterns) - reachable

    assert candidates, (
        f"{render.module}:{render.handler} renders {render.template}, which "
        f"dynamically includes a template via {dynamic}, but no candidates "
        f"could be resolved from the name patterns {sorted(patterns)}. Those "
        "templates would go unscanned - teach _template_name_patterns how the "
        "name is built rather than letting this test silently shrink."
    )

    for candidate in sorted(candidates):
        _referenced_templates(candidate, reachable)
    return reachable


CACHED_PUBLIC_RENDERS: list[RenderedTemplate] = list(_cached_public_renders())


def test_found_cached_public_handlers() -> None:
    # Sanity check that the AST walk above is actually finding handlers, so a
    # refactor that breaks discovery doesn't turn this file into a no-op.
    #
    # These pins are deliberately specific rather than a count threshold. The
    # two decorator forms are discovered by different branches of
    # `_decorator_name`, and dropping either one silently halves coverage while
    # leaving a count comfortably non-zero. Pinning renders from more than one
    # module also catches a walk that collapses to a single file.
    expected = [
        # bare `@cached_public`
        RenderedTemplate(
            "backend/web/handlers/team.py", "team_detail", "team_details.html"
        ),
        # `@cached_public(ttl=...)` call form
        RenderedTemplate("backend/web/handlers/team.py", "team_list", "team_list.html"),
        RenderedTemplate(
            "backend/web/handlers/match.py", "match_detail", "match_details.html"
        ),
        # rendered by a helper `index` delegates to, not by `index` itself
        RenderedTemplate(
            "backend/web/handlers/index.py", "index", "index/index_kickoff.html"
        ),
    ]
    missing = [render for render in expected if render not in CACHED_PUBLIC_RENDERS]
    assert not missing, (
        f"Handler discovery stopped finding {missing}. This test only guards "
        "the handlers it discovers, so a gap here silently shrinks coverage."
    )


@pytest.mark.parametrize(
    "render", CACHED_PUBLIC_RENDERS, ids=lambda r: f"{r.handler}:{r.template}"
)
def test_cached_public_template_has_no_csrf_token(render: RenderedTemplate) -> None:
    offenders = sorted(
        template
        for template in _reachable_templates(render)
        if CSRF_TOKEN_RE.search(_template_source(template))
    )
    assert not offenders, (
        f"{render.module}:{render.handler} is @cached_public but renders "
        f"{render.template}, which references csrf_token via {offenders}. "
        "A per-session CSRF token must not be baked into a publicly cached "
        "page - fetch one from /_/account/info client-side instead. "
        "See https://github.com/the-blue-alliance/the-blue-alliance/issues/10495"
    )
