from flask import Flask
from unittest.mock import patch

from backend.common.middleware import install_middleware
from backend.common.profiler import (
    TraceContext,
    trace_context,
    send_traces,
)


def setup_app():
    app = Flask(__name__)
    install_middleware(app)

    @app.teardown_request
    def teardown_request(exception):
        send_traces()

    return app


@patch("backend.common.profiler._make_tracing_call")
def test_send_trace(mock_send_traces) -> None:
    app = setup_app()

    @app.route("/")
    def route():
        with TraceContext() as root:
            with root.span("test_span"):
                assert len(root._spans) == 1
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
        with TraceContext() as root:
            with root.span("test_span"):
                assert len(root._spans) == 1
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
        with TraceContext() as root:
            assert len(root._spans) == 0
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
        with TraceContext() as root1:
            with root1.span("test_span_1"):
                pass
            with root1.span("test_span_2"):
                pass

        with TraceContext() as root2:
            with root2.span("test_span_3"):
                pass

        assert len(trace_context.request.spans) == 3
        return "Hi!"

    mock_send_traces.assert_not_called()

    with app.test_client() as client:
        client.get("/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"})

    mock_send_traces.assert_called()
