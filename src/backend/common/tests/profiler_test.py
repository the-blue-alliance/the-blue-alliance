from unittest.mock import patch

from flask import Flask

from backend.common.middleware import install_middleware
from backend.common.profiler import Span, trace_context


def setup_app():
    app = Flask(__name__)
    install_middleware(app)
    return app


@patch("backend.common.profiler._make_tracing_call")
def test_send_trace(mock_send_traces) -> None:
    app = setup_app()

    @app.route("/")
    def route():
        with Span("test_span"):
            pass
        assert len(trace_context.request.spans) == 1
        return "Hi!"

    mock_send_traces.assert_not_called()

    with app.test_client() as client:
        client.get("/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"})

    mock_send_traces.assert_called()


@patch("backend.common.profiler._make_tracing_call")
def test_not_send_trace(mock_send_traces) -> None:
    app = setup_app()

    @app.route("/")
    def route():
        with Span("test_span"):
            pass
        assert len(trace_context.request.spans) == 1
        return "Hi!"

    mock_send_traces.assert_not_called()

    with app.test_client() as client:
        client.get("/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=0"})

    mock_send_traces.assert_not_called()


@patch("backend.common.profiler._make_tracing_call")
def test_no_spans(mock_send_traces) -> None:
    app = setup_app()

    @app.route("/")
    def route():
        assert len(trace_context.request.spans) == 0
        return "Hi!"

    mock_send_traces.assert_not_called()

    with app.test_client() as client:
        client.get("/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"})

    mock_send_traces.assert_not_called()


@patch("backend.common.profiler._make_tracing_call")
def test_multiple_spans(mock_send_traces) -> None:
    app = setup_app()

    @app.route("/")
    def route():
        with Span("test_span_1"):
            pass
        with Span("test_span_2"):
            pass
        with Span("test_span_3"):
            pass

        assert len(trace_context.request.spans) == 3
        return "Hi!"

    mock_send_traces.assert_not_called()

    with app.test_client() as client:
        client.get("/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"})

    mock_send_traces.assert_called()
