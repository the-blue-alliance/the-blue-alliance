# From https://medium.com/google-cloud/custom-tracing-in-profiling-gae-using-the-stackdriver-api-b270288622c6

import logging
import random
import time
from contextvars import ContextVar, Token
from datetime import datetime
from typing import Any, cast, Dict, Optional

from werkzeug.local import Local

from backend.common.environment import Environment
from backend.common.tasklets import enable_tasklet_context_propagation

enable_tasklet_context_propagation()

# create a request-local global context
trace_context = Local()
_active_span_var: ContextVar[Optional["Span"]] = ContextVar(
    "active_span", default=cast(Optional["Span"], None)
)

PROJECT_ID = Environment.project()


def send_traces() -> None:
    try:
        request = getattr(trace_context, "request", None)
        spans = getattr(request, "spans", None)
        if not spans:
            return

        _make_tracing_call(
            {
                "traces": [
                    {
                        "projectId": PROJECT_ID,
                        "traceId": request.trace_id,
                        "spans": spans,
                    }
                ]
            }
        )
    except Exception as e:
        logging.warning("send_traces() failed!")
        logging.exception(e)


def _make_tracing_call(body: Dict[str, Any]) -> None:
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


class Span:
    def __init__(self, name: str) -> None:
        """
        Start a Span
        Spans are saved in trace_context.request.spans on exit
        Spans are sent by send_traces() which is called when the request context ends
        """
        self._name = name
        self._labels: Dict[str, str] = {}  # Cloud Trace spans support labels
        self._span_id = str(random.getrandbits(64))
        self._root_span_id: Optional[str] = None
        self._parent_span_id: Optional[str] = None
        self._token: Optional[Token[Optional["Span"]]] = None
        self._startTime: Optional[datetime] = None
        self._endTime: Optional[datetime] = None
        self._start_cpu: Optional[float] = None

        if hasattr(trace_context, "request") and trace_context.request:
            tcontext = trace_context.request.headers.get(
                "X-Cloud-Trace-Context", "NNNN/NNNN;xxxxx"
            )
            self._do_trace = ";o=1" in tcontext
            if self._do_trace:
                logging.debug("Trace Context: {}".format(tcontext))

            # Breakup our given cloud tracing context so we can get the flags out of it
            trace_id, root_span_id = tcontext.split(";")[0].split("/")
            trace_context.request.trace_id = trace_id
            self._root_span_id = root_span_id

        else:
            self._do_trace = False

        parent = _active_span_var.get()
        self._parent_span_id = parent._span_id if parent else self._root_span_id

    @property
    def span_id(self) -> str:
        return self._span_id

    @property
    def parent_span_id(self) -> Optional[str]:
        return self._parent_span_id

    def set_label(self, key: str, value: str) -> None:
        """
        Add a label to this span. Labels are key-value pairs that appear in Cloud Trace.
        They help with filtering and analyzing traces in the GCP Console.

        Args:
            key: Label key (e.g., "api_key", "user_id")
            value: Label value (will be converted to string)
        """
        self._labels[key] = str(value)

    def __enter__(self) -> "Span":
        if self._do_trace:
            logging.debug("CREATED SPAN: {}".format(self._name))
        parent = _active_span_var.get()
        self._parent_span_id = parent._span_id if parent else self._root_span_id
        self._token = _active_span_var.set(self)
        self._startTime = datetime.now()
        if self._do_trace:
            self._start_cpu = time.thread_time()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._endTime = datetime.now()
        if self._token is not None:
            try:
                _active_span_var.reset(self._token)
            except ValueError:
                pass
            self._token = None

        if self._do_trace and exc_type is not GeneratorExit:
            start_cpu = self._start_cpu
            start_time = self._startTime
            end_time = self._endTime
            if (
                start_cpu is not None
                and start_time is not None
                and end_time is not None
            ):
                cpu_duration_ms = (time.thread_time() - start_cpu) * 1000.0
                self.set_label("cpu_time_ms", f"{cpu_duration_ms:.2f}")

                wall_duration_ms = (end_time - start_time).total_seconds() * 1000.0
                self.set_label("wall_time_ms", f"{wall_duration_ms:.2f}")
                if wall_duration_ms > 0:
                    cpu_ratio = min(1.0, cpu_duration_ms / wall_duration_ms)
                    self.set_label("cpu_ratio", f"{cpu_ratio:.2f}")

            request = getattr(trace_context, "request", None)
            if request is not None:
                if not hasattr(request, "spans"):
                    request.spans = []
                request.spans.append(self.dict())

    def dict(self) -> Dict[str, Any]:
        """Format as a dictionary of the correct shape for sending to the Cloud
        Trace REST API as a JSON object"""
        span_dict = {
            "kind": "SPAN_KIND_UNSPECIFIED",
            "name": self._name,
            "parentSpanId": self._parent_span_id,
            "spanId": self._span_id,
            "startTime": (self._startTime.isoformat() + "Z") if self._startTime else "",
            "endTime": (self._endTime.isoformat() + "Z") if self._endTime else "",
        }

        # Add labels if any were set
        if self._labels:
            span_dict["labels"] = self._labels

        return span_dict
