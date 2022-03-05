import datetime

from backend.web.context_processors import render_time_context_processor


def test_render_time_context_processor() -> None:
    render_time_context = render_time_context_processor()
    assert type(render_time_context["render_time"]) is datetime.datetime
