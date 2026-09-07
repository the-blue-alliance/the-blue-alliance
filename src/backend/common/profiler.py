# From https://medium.com/google-cloud/custom-tracing-in-profiling-gae-using-the-stackdriver-api-b270288622c6

import logging
import random
from datetime import datetime
from typing import Optional

from werkzeug.local import Local

from backend.common.environment import Environment

# create a request-local global context
trace_context = Local()

PROJECT_ID = Environment.project()


def _init_request_trace_context() -> None:
    """Safely extracts trace_id, root_span_id, and sampling flag from request headers."""
    req = getattr(trace_context, "request", None)
    if req is not None and not hasattr(req, "trace_id"):
        tcontext = req.headers.get("X-Cloud-Trace-Context", "NNNN/NNNN;xxxxx")
        # Header format: TRACE_ID/SPAN_ID;o=TRACE_TRUE
        parts = tcontext.split(";")[0].split("/")
        req.trace_id = parts[0] if len(parts) > 0 and parts[0] else None
        req.root_span_id = parts[1] if len(parts) > 1 and parts[1] else None
        req._trace_sampled = ";o=1" in tcontext


def get_current_span() -> Optional["Span"]:
    """Returns the currently active Span in the current context, if any."""
    span = getattr(trace_context, "current_span", None)
    while span is not None and getattr(span, "_endTime", None) is not None:
        span = span._previous_span
    trace_context.current_span = span
    return span


def send_traces():
    try:
        if (
            not hasattr(trace_context.request, "spans")
            or len(trace_context.request.spans) == 0
        ):
            return

        _make_tracing_call(
            {
                "traces": [
                    {
                        "projectId": PROJECT_ID,
                        "traceId": trace_context.request.trace_id,
                        "spans": trace_context.request.spans,
                    }
                ]
            }
        )
    except Exception as e:
        logging.warning("send_traces() failed!")
        logging.exception(e)


def _make_tracing_call(body):
    if PROJECT_ID is None:
        return

    from googleapiclient import discovery
    from oauth2client.client import GoogleCredentials

    # Authentication is provided by the 'gcloud' tool when running locally
    # and by built-in service accounts when running on GAE, GCE, or GKE.
    # See https://developers.google.com/identity/protocols/application-default-credentials for more information.
    credentials = GoogleCredentials.get_application_default()

    # Construct the cloudtrace service object (version v1) for interacting
    # with the API. You can browse other available API services and versions at
    # https://developers.google.com/api-client-library/python/apis/
    service = discovery.build(
        "cloudtrace", "v1", credentials=credentials, cache_discovery=False
    )

    # Actually submit the patched tracing data.
    request = service.projects().patchTraces(projectId=PROJECT_ID, body=body)
    request.execute()


class Span(object):
    def __init__(self, name: str):
        """
        Start a Span
        Spans are saved in trace_context.request.spans on exit
        Spans are sent by send_traces() which is called when the request context ends
        """
        self._name = name
        self._labels: dict[str, str] = {}  # Cloud Trace spans support labels
        self._span_id: str = str(random.getrandbits(64))
        self._parent_span_id: Optional[str] = None
        self._previous_span: Optional["Span"] = None
        self._root_span_id: Optional[str] = None
        self._startTime: Optional[datetime] = None
        self._endTime: Optional[datetime] = None

        if hasattr(trace_context, "request") and trace_context.request:
            _init_request_trace_context()
            self._do_trace = getattr(trace_context.request, "_trace_sampled", False)
            if self._do_trace:
                tcontext = trace_context.request.headers.get(
                    "X-Cloud-Trace-Context", ""
                )
                logging.debug("Trace Context: {}".format(tcontext))
            self._root_span_id = getattr(trace_context.request, "root_span_id", None)
        else:
            self._do_trace = False

    @property
    def span_id(self) -> str:
        return self._span_id

    @property
    def span_id_hex(self) -> str:
        try:
            return f"{int(self._span_id):016x}"
        except (ValueError, TypeError):
            return self._span_id

    def set_label(self, key: str, value: str) -> None:
        """
        Add a label to this span. Labels are key-value pairs that appear in Cloud Trace.
        They help with filtering and analyzing traces in the GCP Console.

        Args:
            key: Label key (e.g., "api_key", "user_id")
            value: Label value (will be converted to string)
        """
        self._labels[key] = str(value)

    def __enter__(self):
        prev = get_current_span()
        while prev is self:
            prev = prev._previous_span

        self._previous_span = prev
        self._startTime = datetime.now()
        self._endTime = None
        trace_context.current_span = self

        if self._previous_span is not None:
            self._parent_span_id = self._previous_span.span_id
        else:
            self._parent_span_id = self._root_span_id

        if self._do_trace:
            logging.debug("CREATED SPAN: {}".format(self._name))
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self._endTime = datetime.now()
        try:
            if exc_type is not None:
                self.set_label("/error/name", exc_type.__name__)
                self.set_label("/error/status", exc_type.__name__)
                self.set_label("/error/message", str(exc_value))
                import traceback

                tb_str = "".join(traceback.format_exception(exc_type, exc_value, tb))
                # Cloud Trace label value limit is 16 KiB (16,384 bytes)
                self.set_label("/stacktrace", tb_str[:16000])
        finally:
            get_current_span()

        if self._do_trace:
            if not hasattr(trace_context.request, "spans"):
                trace_context.request.spans = []
            trace_context.request.spans.append(self.dict())

    def dict(self):
        """Format as a dictionary of the correct shape for sending to the Cloud
        Trace REST API as a JSON object"""
        span_dict = {
            "kind": "SPAN_KIND_UNSPECIFIED",
            "name": self._name,
            "parentSpanId": self._parent_span_id or self._root_span_id,
            "spanId": self._span_id,
            "startTime": self._startTime.isoformat() + "Z" if self._startTime else "",
            "endTime": self._endTime.isoformat() + "Z" if self._endTime else "",
        }

        # Add labels if any were set
        if self._labels:
            span_dict["labels"] = self._labels

        return span_dict
