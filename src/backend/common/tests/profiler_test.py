import contextvars
import gc
from unittest.mock import patch

from flask import Flask
from google.appengine.ext import ndb

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


@patch("backend.common.profiler._make_tracing_call")
def test_concurrent_tasklet_spans_are_siblings(mock_send_traces) -> None:
    app = setup_app()

    @ndb.tasklet
    def async_query(name: str):
        with Span(f"{name}.fetch_async"):
            yield ndb.sleep(0.01)

    @app.route("/")
    def route():
        f1 = async_query("Query1")
        f2 = async_query("Query2")
        f3 = async_query("Query3")
        ndb.Future.wait_all([f1, f2, f3])

        spans = trace_context.request.spans
        assert len(spans) == 3

        q1_span = next(s for s in spans if s["name"] == "Query1.fetch_async")
        q2_span = next(s for s in spans if s["name"] == "Query2.fetch_async")
        q3_span = next(s for s in spans if s["name"] == "Query3.fetch_async")

        assert q1_span["parentSpanId"] == "SPAN_ID"
        assert q2_span["parentSpanId"] == "SPAN_ID"
        assert q3_span["parentSpanId"] == "SPAN_ID"
        return "Hi!"

    with app.test_client() as client:
        client.get("/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"})
        send_traces()

    mock_send_traces.assert_called_once()


@patch("backend.common.profiler._make_tracing_call")
def test_span_cpu_tracking(mock_send_traces) -> None:
    app = setup_app()

    @app.route("/")
    def route():
        with Span("cpu_span"):
            # Burn a tiny bit of CPU cycles
            _ = sum(i * i for i in range(1000))
        assert len(trace_context.request.spans) == 1
        s_dict = trace_context.request.spans[0]
        assert "labels" in s_dict
        assert "cpu_time_ms" in s_dict["labels"]
        assert "wall_time_ms" in s_dict["labels"]
        assert "cpu_ratio" in s_dict["labels"]
        # Verify values are valid floats
        assert float(s_dict["labels"]["cpu_time_ms"]) >= 0.0
        assert float(s_dict["labels"]["wall_time_ms"]) >= 0.0
        assert 0.0 <= float(s_dict["labels"]["cpu_ratio"]) <= 1.0
        return "OK"

    with app.test_client() as client:
        client.get("/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"})
        send_traces()

    mock_send_traces.assert_called_once()


@patch("backend.common.profiler._make_tracing_call")
def test_tasklet_child_spans_are_nested(mock_send_traces) -> None:
    app = setup_app()

    @ndb.tasklet
    def do_query(name: str):
        with Span(f"{name}._do_query"):
            yield ndb.sleep(0.01)

    @ndb.tasklet
    def fetch_async(name: str):
        with Span(f"{name}.fetch_async"):
            yield do_query(name)

    @app.route("/")
    def route():
        f1 = fetch_async("Query1")
        f2 = fetch_async("Query2")
        ndb.Future.wait_all([f1, f2])

        spans = trace_context.request.spans
        assert len(spans) == 4

        q1_fetch = next(s for s in spans if s["name"] == "Query1.fetch_async")
        q1_do = next(s for s in spans if s["name"] == "Query1._do_query")
        q2_fetch = next(s for s in spans if s["name"] == "Query2.fetch_async")
        q2_do = next(s for s in spans if s["name"] == "Query2._do_query")

        # Top-level query spans are siblings under root span
        assert q1_fetch["parentSpanId"] == "SPAN_ID"
        assert q2_fetch["parentSpanId"] == "SPAN_ID"

        # Inner _do_query spans are nested under their respective fetch_async spans
        assert q1_do["parentSpanId"] == q1_fetch["spanId"]
        assert q2_do["parentSpanId"] == q2_fetch["spanId"]
        return "Hi!"

    with app.test_client() as client:
        client.get("/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"})
        send_traces()

    mock_send_traces.assert_called_once()


@patch("backend.common.profiler._make_tracing_call")
def test_tasklet_exception_unwinds_span(mock_send_traces) -> None:
    app = setup_app()

    @ndb.tasklet
    def failing_tasklet():
        with Span("failing_async"):
            yield ndb.sleep(0.01)
            raise ValueError("Tasklet error")

    @app.route("/")
    def route():
        try:
            failing_tasklet().get_result()
        except ValueError:
            pass

        with Span("after_exception"):
            pass

        spans = trace_context.request.spans
        assert len(spans) == 2

        failing_span = next(s for s in spans if s["name"] == "failing_async")
        after_span = next(s for s in spans if s["name"] == "after_exception")

        assert failing_span["parentSpanId"] == "SPAN_ID"
        assert after_span["parentSpanId"] == "SPAN_ID"
        return "Hi!"

    with app.test_client() as client:
        client.get("/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"})
        send_traces()

    mock_send_traces.assert_called_once()


def test_span_generator_exit_handling() -> None:
    app = setup_app()

    def sample_generator():
        with Span("gen_span"):
            yield 1
            yield 2

    @app.route("/")
    def route():
        gen = sample_generator()
        assert next(gen) == 1
        gen.close()
        spans = getattr(trace_context.request, "spans", [])
        assert len(spans) == 0
        return "Hi!"

    with app.test_client() as client:
        client.get("/", headers={"X-Cloud-Trace-Context": "TRACE_ID/SPAN_ID;o=1"})
        send_traces()


def test_span_generator_gc_cross_context() -> None:
    def sample_generator():
        with Span("gen_span"):
            yield 1

    ctx = contextvars.copy_context()
    gen = ctx.run(sample_generator)
    assert next(gen) == 1
    del gen
    gc.collect()


def test_span_exit_without_request() -> None:
    trace_context.request = None
    with Span("no_request_span"):
        pass
