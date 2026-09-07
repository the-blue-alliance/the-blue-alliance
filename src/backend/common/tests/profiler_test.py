from unittest.mock import patch

from flask import Flask

from backend.common.middleware import install_middleware
from backend.common.profiler import send_traces, Span, trace_context


def setup_app():
    app = Flask(__name__)
    app.testing = True
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
        resp = client.get(
            "/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"}
        )
        assert resp.status_code == 200
        send_traces()

    mock_send_traces.assert_called()


@patch("backend.common.profiler._make_tracing_call")
def test_not_send_trace(mock_send_traces) -> None:
    app = setup_app()

    @app.route("/")
    def route():
        with Span("test_span"):
            pass
        assert (
            not hasattr(trace_context.request, "spans")
            or len(trace_context.request.spans) == 0
        )
        return "Hi!"

    mock_send_traces.assert_not_called()

    with app.test_client() as client:
        resp = client.get(
            "/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=0"}
        )
        assert resp.status_code == 200
        send_traces()

    mock_send_traces.assert_not_called()


@patch("backend.common.profiler._make_tracing_call")
def test_no_spans(mock_send_traces) -> None:
    app = setup_app()

    @app.route("/")
    def route():
        assert (
            not hasattr(trace_context.request, "spans")
            or len(trace_context.request.spans) == 0
        )
        return "Hi!"

    mock_send_traces.assert_not_called()

    with app.test_client() as client:
        resp = client.get(
            "/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"}
        )
        assert resp.status_code == 200
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
        resp = client.get(
            "/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"}
        )
        assert resp.status_code == 200
        send_traces()

    mock_send_traces.assert_called()


@patch("backend.common.profiler._make_tracing_call")
def test_span_hierarchy(mock_send_traces) -> None:
    from backend.common.profiler import get_current_span

    app = setup_app()

    @app.route("/")
    def route():
        assert get_current_span() is None
        with Span("parent") as parent:
            assert get_current_span() is parent
            with Span("child") as child:
                assert get_current_span() is child
                with Span("grandchild") as grandchild:
                    assert get_current_span() is grandchild
                assert get_current_span() is child
            assert get_current_span() is parent
        assert get_current_span() is None

        spans = trace_context.request.spans
        assert len(spans) == 3
        # Exit order is grandchild, child, parent
        grandchild_dict, child_dict, parent_dict = spans[0], spans[1], spans[2]

        assert parent_dict["name"] == "parent"
        assert parent_dict["parentSpanId"] == "SPAN_ID"

        assert child_dict["name"] == "child"
        assert child_dict["parentSpanId"] == parent_dict["spanId"]

        assert grandchild_dict["name"] == "grandchild"
        assert grandchild_dict["parentSpanId"] == child_dict["spanId"]
        return "Hi!"

    with app.test_client() as client:
        resp = client.get(
            "/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"}
        )
        assert resp.status_code == 200


@patch("backend.common.profiler._make_tracing_call")
def test_span_error_capture(mock_send_traces) -> None:
    import pytest
    from backend.common.profiler import get_current_span

    app = setup_app()

    @app.route("/")
    def route():
        with pytest.raises(ValueError, match="test error"):
            with Span("failing_span"):
                raise ValueError("test error")

        assert get_current_span() is None
        spans = trace_context.request.spans
        assert len(spans) == 1
        error_span = spans[0]
        assert error_span["labels"]["/error/name"] == "ValueError"
        assert error_span["labels"]["/error/status"] == "ValueError"
        assert error_span["labels"]["/error/message"] == "test error"
        assert "/stacktrace" in error_span["labels"]
        assert "ValueError: test error" in error_span["labels"]["/stacktrace"]
        return "Hi!"

    with app.test_client() as client:
        resp = client.get(
            "/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"}
        )
        assert resp.status_code == 200


@patch("backend.common.profiler._make_tracing_call")
def test_span_hierarchy_out_of_order_exit(mock_send_traces) -> None:
    """Test that if spans exit out-of-order (e.g. concurrent tasklets),

    dead spans are unwound and current_span is not left pointing to a closed span.
    """
    from backend.common.profiler import get_current_span

    app = setup_app()

    @app.route("/")
    def route():
        # Simulate two concurrent coroutines with overlapping spans:
        # Coroutine 1 enters span1
        s1 = Span("coroutine_1")
        s1.__enter__()
        assert get_current_span() is s1

        # Coroutine 2 enters span2 while span1 is still open
        s2 = Span("coroutine_2")
        s2.__enter__()
        assert get_current_span() is s2

        # Coroutine 1 finishes first and exits span1
        s1.__exit__(None, None, None)
        # Span 2 is still running and active
        assert get_current_span() is s2

        # Coroutine 2 finishes and exits span2
        s2.__exit__(None, None, None)
        # Because span1 already ended, current_span must NOT be left pointing to span1!
        assert get_current_span() is None

        return "Hi!"

    with app.test_client() as client:
        resp = client.get(
            "/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"}
        )
        assert resp.status_code == 200


@patch("backend.common.profiler._make_tracing_call")
def test_span_domain_labels(mock_send_traces) -> None:
    app = setup_app()

    @app.route("/")
    def route():
        with Span("labeled_span") as span:
            span.set_label("cache_hit", "hit")
            span.set_label("model", "Event")

        spans = trace_context.request.spans
        assert len(spans) == 1
        assert spans[0]["labels"]["cache_hit"] == "hit"
        assert spans[0]["labels"]["model"] == "Event"
        return "Hi!"

    with app.test_client() as client:
        resp = client.get(
            "/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"}
        )
        assert resp.status_code == 200


def test_span_reuse() -> None:
    from backend.common.profiler import get_current_span

    app = setup_app()

    @app.route("/")
    def route():
        s = Span("reused_span")
        with s:
            assert get_current_span() is s
        assert get_current_span() is None

        # Re-entering the same Span instance
        with s:
            assert get_current_span() is s
        assert get_current_span() is None
        return "Hi!"

    with app.test_client() as client:
        resp = client.get(
            "/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"}
        )
        assert resp.status_code == 200


def test_span_recursive_entry() -> None:
    from backend.common.profiler import get_current_span

    app = setup_app()

    @app.route("/")
    def route():
        s = Span("recursive_span")
        with s:
            assert get_current_span() is s
            with s:
                assert get_current_span() is s
            assert get_current_span() is None
        assert get_current_span() is None
        return "Hi!"

    with app.test_client() as client:
        resp = client.get(
            "/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"}
        )
        assert resp.status_code == 200
