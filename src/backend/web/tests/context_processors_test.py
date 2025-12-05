from datetime import datetime, timezone

from backend.web.context_processors import render_time_context_processor


def test_render_time_context_processor() -> None:
    render_time_context = render_time_context_processor()
    render_time = render_time_context["render_time"]
    assert isinstance(render_time, datetime)
    assert render_time.tzinfo == timezone.utc  # pyre-ignore[16]
