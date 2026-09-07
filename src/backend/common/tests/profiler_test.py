from unittest.mock import patch

from flask import Flask

from backend.common.middleware import install_middleware
from backend.common.profiler import send_traces, Span, trace_context


def setup_app():
    app = Flask(__name__)
    install_middleware(app, configure_secret_key=False)
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
        send_traces()

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
        send_traces()

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
        send_traces()

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
        send_traces()

    mock_send_traces.assert_called()


@patch("backend.common.profiler._make_tracing_call")
def test_nested_spans(mock_send_traces) -> None:
    app = setup_app()

    @app.route("/")
    def route():
        with Span("parent") as parent:
            with Span("child") as child:
                with Span("grandchild") as grandchild:
                    pass

        spans = trace_context.request.spans
        assert len(spans) == 3

        grandchild_span = next(s for s in spans if s["name"] == "grandchild")
        child_span = next(s for s in spans if s["name"] == "child")
        parent_span = next(s for s in spans if s["name"] == "parent")

        assert parent_span["parentSpanId"] == "SPAN_ID"
        assert child_span["parentSpanId"] == parent.span_id
        assert grandchild_span["parentSpanId"] == child.span_id
        assert len({parent.span_id, child.span_id, grandchild.span_id}) == 3
        return "Hi!"

    mock_send_traces.assert_not_called()

    with app.test_client() as client:
        client.get("/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"})
        send_traces()

    mock_send_traces.assert_called_once()
    body = mock_send_traces.call_args[0][0]
    trace_spans = body["traces"][0]["spans"]
    assert len(trace_spans) == 3


@patch("backend.common.profiler._make_tracing_call")
def test_sibling_nested_spans(mock_send_traces) -> None:
    app = setup_app()

    @app.route("/")
    def route():
        with Span("parent") as parent:
            with Span("child_1"):
                pass
            with Span("child_2"):
                pass
        with Span("top_level_2"):
            pass

        spans = trace_context.request.spans
        assert len(spans) == 4

        child1_span = next(s for s in spans if s["name"] == "child_1")
        child2_span = next(s for s in spans if s["name"] == "child_2")
        parent_span = next(s for s in spans if s["name"] == "parent")
        top2_span = next(s for s in spans if s["name"] == "top_level_2")

        assert parent_span["parentSpanId"] == "SPAN_ID"
        assert child1_span["parentSpanId"] == parent.span_id
        assert child2_span["parentSpanId"] == parent.span_id
        assert top2_span["parentSpanId"] == "SPAN_ID"
        return "Hi!"

    with app.test_client() as client:
        client.get("/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"})
        send_traces()

    mock_send_traces.assert_called_once()


@patch("backend.common.profiler._make_tracing_call")
def test_nested_span_exception_unwinds_stack(mock_send_traces) -> None:
    app = setup_app()

    @app.route("/")
    def route():
        try:
            with Span("parent"):
                with Span("failing_child"):
                    raise RuntimeError("Something failed")
        except RuntimeError:
            pass

        with Span("after_exception"):
            pass

        spans = trace_context.request.spans
        assert len(spans) == 3

        after_span = next(s for s in spans if s["name"] == "after_exception")
        parent_span = next(s for s in spans if s["name"] == "parent")
        failing_span = next(s for s in spans if s["name"] == "failing_child")

        assert parent_span["parentSpanId"] == "SPAN_ID"
        assert failing_span["parentSpanId"] == parent_span["spanId"]
        assert after_span["parentSpanId"] == "SPAN_ID"
        return "Hi!"

    with app.test_client() as client:
        client.get("/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"})
        send_traces()

    mock_send_traces.assert_called_once()


def test_standalone_span_hierarchy() -> None:
    trace_context.request = None
    with Span("parent") as parent:
        assert parent.parent_span_id is None
        with Span("child") as child:
            assert child.parent_span_id == parent.span_id
            with Span("grandchild") as grandchild:
                assert grandchild.parent_span_id == child.span_id
    assert parent.span_id != child.span_id != grandchild.span_id

    grandchild_dict = grandchild.dict()
    child_dict = child.dict()
    parent_dict = parent.dict()

    assert grandchild_dict["parentSpanId"] == child.span_id
    assert child_dict["parentSpanId"] == parent.span_id
    assert parent_dict["parentSpanId"] is None
