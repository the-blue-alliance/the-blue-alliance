from unittest.mock import patch

from backend.common.profiler import TraceContext, trace_context


class FakeRequest(object):
    def __init__(self, headers):
        self.headers = headers


@patch("backend.common.profiler.send_trace")
def test_send_trace(mock_send_trace) -> None:
    trace_context.request = FakeRequest(
        {"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"}
    )

    mock_send_trace.assert_not_called()

    with TraceContext() as root:
        with root.span("test_span"):
            pass

    mock_send_trace.assert_called()


@patch("backend.common.profiler.send_trace")
def test_not_send_trace(mock_send_trace) -> None:
    trace_context.request = FakeRequest(
        {"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=0"}
    )

    mock_send_trace.assert_not_called()

    with TraceContext() as root:
        with root.span("test_span"):
            pass

    mock_send_trace.assert_not_called()
