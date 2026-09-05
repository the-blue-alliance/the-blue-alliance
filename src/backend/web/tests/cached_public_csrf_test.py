"""
Guards against https://github.com/the-blue-alliance/the-blue-alliance/issues/10495.

`cached_public` keys its cache on path + query string only, with no user
component, so the rendered HTML body is stored once and served to every
visitor. A CSRF token is per-session, so rendering `csrf_token()` into a
publicly cached page hands whichever token warmed the cache to everyone else,
and their POSTs are rejected with a 400.

This test walks every web handler decorated with `cached_public`, resolves the
templates it renders (transitively through extends/include/import), and asserts
none of them reference `csrf_token`. Client-side code that needs a token should
fetch one from `/_/account/info` instead.
"""

import ast
import re
from pathlib import Path
from typing import Iterator, List, NamedTuple, Optional, Set

import pytest
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from jinja2 import meta as jinja_meta

WEB_ROOT = Path(__file__).resolve().parents[1]
HANDLERS_ROOT = WEB_ROOT / "handlers"
TEMPLATES_ROOT = WEB_ROOT / "templates"

CSRF_TOKEN_RE = re.compile(r"\bcsrf_token\b")

_jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_ROOT)))


class RenderedTemplate(NamedTuple):
    module: str
    handler: str
    template: str


def _decorator_name(node: ast.expr) -> Optional[str]:
    # Handles @cached_public, @cached_public(ttl=...), and @module.cached_public
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _called_name(node: ast.Call) -> Optional[str]:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _cached_public_renders() -> Iterator[RenderedTemplate]:
    for path in sorted(HANDLERS_ROOT.rglob("*.py")):
        if "tests" in path.parts:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        module = str(path.relative_to(WEB_ROOT.parent.parent))
        for func in ast.walk(tree):
            if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not any(
                _decorator_name(d) == "cached_public" for d in func.decorator_list
            ):
                continue
            for call in ast.walk(func):
                if not isinstance(call, ast.Call):
                    continue
                if _called_name(call) != "render_template":
                    continue
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


def _referenced_templates(template: str, seen: Set[str]) -> Set[str]:
    """All templates reachable from `template` via extends/include/import."""
    if template in seen:
        return seen
    seen.add(template)
    parsed = _jinja_env.parse(_template_source(template))
    for referenced in jinja_meta.find_referenced_templates(parsed):
        if referenced is None:
            # A dynamic {% include some_var %} - can't follow it
            continue
        _referenced_templates(referenced, seen)
    return seen


CACHED_PUBLIC_RENDERS: List[RenderedTemplate] = list(_cached_public_renders())


def test_found_cached_public_handlers() -> None:
    # Sanity check that the AST walk above is actually finding handlers, so a
    # refactor that breaks the discovery doesn't turn this file into a no-op.
    assert len(CACHED_PUBLIC_RENDERS) > 10
    assert (
        RenderedTemplate(
            "backend/web/handlers/team.py", "team_detail", "team_details.html"
        )
        in CACHED_PUBLIC_RENDERS
    )


@pytest.mark.parametrize(
    "render", CACHED_PUBLIC_RENDERS, ids=lambda r: f"{r.handler}:{r.template}"
)
def test_cached_public_template_has_no_csrf_token(render: RenderedTemplate) -> None:
    offenders = sorted(
        template
        for template in _referenced_templates(render.template, set())
        if CSRF_TOKEN_RE.search(_template_source(template))
    )
    assert not offenders, (
        f"{render.module}:{render.handler} is @cached_public but renders "
        f"{render.template}, which references csrf_token via {offenders}. "
        "A per-session CSRF token must not be baked into a publicly cached "
        "page - fetch one from /_/account/info client-side instead. "
        "See https://github.com/the-blue-alliance/the-blue-alliance/issues/10495"
    )
