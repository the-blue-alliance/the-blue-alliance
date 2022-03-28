from datetime import datetime, timezone

from backend.web.context_processors import render_time_context_processor


def test_render_time_context_processor() -> None:
    render_time_context = render_time_context_processor()
    render_time = render_time_context["render_time"]
    assert type(render_time) is datetime
    assert render_time.tzinfo == timezone.utc
