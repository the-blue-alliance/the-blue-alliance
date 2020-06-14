# From https://medium.com/google-cloud/custom-tracing-in-profiling-gae-using-the-stackdriver-api-b270288622c6

import logging
import os
import random
from datetime import datetime

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from werkzeug.local import Local


# create a request-local global context
trace_context = Local()

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", None)


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

        if hasattr(trace_context, "request") and trace_context.request:
            tcontext = trace_context.request.headers.get(
                "X-Cloud-Trace-Context", "NNNN/NNNN;xxxxx"
            )
            self._do_trace = ";o=1" in tcontext
            if self._do_trace:
                logging.info("Trace Context: {}".format(tcontext))

            # Breakup our given cloud tracing context so we can get the flags out of it
            trace_id, root_span_id = tcontext.split(";")[0].split("/")
            trace_context.request.trace_id = trace_id
            self._root_span_id = root_span_id

        else:
            self._do_trace = False

    def __enter__(self):
        if self._do_trace:
            logging.info("CREATED SPAN: {}".format(self._name))
        self._startTime = datetime.now()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._endTime = datetime.now()
        if self._do_trace:
            if not hasattr(trace_context.request, "spans"):
                trace_context.request.spans = []
            trace_context.request.spans.append(self.dict())

    def dict(self):
        """Format as a dictionary of the correct shape for sending to the Cloud
        Trace REST API as a JSON object"""
        return {
            "kind": "SPAN_KIND_UNSPECIFIED",
            "name": self._name,
            "parentSpanId": self._root_span_id,
            "spanId": str(random.getrandbits(64)),
            "startTime": self._startTime.isoformat() + "Z",
            "endTime": self._endTime.isoformat() + "Z",
        }
