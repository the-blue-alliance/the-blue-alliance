# From https://medium.com/google-cloud/custom-tracing-in-profiling-gae-using-the-stackdriver-api-b270288622c6

from datetime import datetime
import logging
import os
import random
from werkzeug.local import Local

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials


# create a request-local global context
trace_context = Local()

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", None)


def send_request_context_traces():
    # Grab our spans object as a json blob
    spans = [s.json() for s in trace_context.request.spans]

    for s in spans:
        s["parentSpanId"] = trace_context.request.root_span_id

    traces_body = {
        "projectId": PROJECT_ID,
        "traceId": trace_context.request.trace_id,
        "spans": spans,
    }
    body = {"traces": [traces_body]}

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
    def __init__(self, name: str, doTrace: bool, kind: str = "SPAN_KIND_UNSPECIFIED"):
        self.id = str(random.getrandbits(64))
        self.name = name
        self.doTrace = doTrace
        self.kind = kind

    # Helpers for scope-specific use cases
    def __enter__(self):
        if self.doTrace:
            logging.info("CREATED SPAN: {}".format(self.name))
        self.startTime = datetime.now()
        return self

    def __exit__(self, type, value, tb):
        self.endTime = datetime.now()

    def json(self):
        """Format as a dictionary of the correct shape for sending to the Cloud
        Trace REST API as a JSON object"""
        j = {
            "kind": self.kind,
            "name": self.name,
            "spanId": self.id,
            "startTime": self.startTime.isoformat() + "Z",
            "endTime": self.endTime.isoformat() + "Z",
        }
        return j


class TraceContext(object):
    def __init__(self):
        """
        Start a TraceContext
        Spans are saved in trace_context.request.spans on exit
        Spans are sent by send_context_traces() which is called when the request context ends
        """
        self._spans = []

        if hasattr(trace_context, "request") and trace_context.request:
            tcontext = trace_context.request.headers.get(
                "X-Cloud-Trace-Context", "NNNN/NNNN;xxxxx"
            )
            self._do_trace = ";o=1" in tcontext

            # Breakup our given cloud tracing context so we can get the flags out of it
            trace_id, root_span_id = tcontext.split(";")[0].split("/")
            trace_context.request.trace_id = trace_id
            trace_context.request.root_span_id = root_span_id
        else:
            self._do_trace = False
        self._do_trace = True  # TODO: remove

        if self._do_trace:
            logging.info("Trace Context: {}".format(tcontext))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not hasattr(trace_context.request, "spans"):
            trace_context.request.spans = []
        trace_context.request.spans += self._spans

    def span(self, name: str = ""):
        spn = Span(name, self._do_trace)
        if self._do_trace:
            self._spans.append(spn)
        return spn
