from datetime import datetime, timezone

import pytest

from backend.web.context_processors import (
    pwa_url_context_processor,
    render_time_context_processor,
)


def test_render_time_context_processor() -> None:
    render_time_context = render_time_context_processor()
    render_time = render_time_context["render_time"]
    assert isinstance(render_time, datetime)
    assert render_time.tzinfo == timezone.utc  # pyre-ignore[16]


def test_pwa_url_context_processor_prod(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "standard")
    context = pwa_url_context_processor()
    assert context["pwa_base_url"] == "https://beta.thebluealliance.com"
    assert (
        context["pwa_suggestion_review_url"]
        == "https://beta.thebluealliance.com/suggest/review"
    )


def test_pwa_url_context_processor_local_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GAE_ENV", "localdev")
    context = pwa_url_context_processor()
    assert context["pwa_base_url"] == "http://localhost:5173"
    assert (
        context["pwa_suggestion_review_url"] == "http://localhost:5173/suggest/review"
    )
