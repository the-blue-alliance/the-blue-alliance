# From https://medium.com/google-cloud/custom-tracing-in-profiling-gae-using-the-stackdriver-api-b270288622c6

from datetime import datetime
import logging
import random
import threading

from google.appengine.api import app_identity
from google.appengine.ext import deferred
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials


# create a thread-local global context
trace_context = threading.local()


# used for deferred call
def send_trace(projectId, trace_body):
    # Authentication is provided by the 'gcloud' tool when running locally
    # and by built-in service accounts when running on GAE, GCE, or GKE.
    # See https://developers.google.com/identity/protocols/application-default-credentials for more information.
    credentials = GoogleCredentials.get_application_default()

    # Construct the cloudtrace service object (version v1) for interacting
    # with the API. You can browse other available API services and versions at
    # https://developers.google.com/api-client-library/python/apis/
    service = discovery.build('cloudtrace', 'v1', credentials=credentials)

    # Actually submit the patched tracing data.
    request = service.projects().patchTraces(projectId=projectId, body=trace_body)
    request.execute()


class Span(object):
    def __init__(self, name, doTrace, kind='SPAN_KIND_UNSPECIFIED'):
        self.id = str(random.getrandbits(64))
        self.name = name
        self.doTrace = doTrace
        self.kind = kind

    def start(self):
        if self.doTrace:
            logging.info("CREATED SPAN: {}".format(self.name))
        self.startTime = datetime.now()

    def finish(self):
        self.endTime = datetime.now()

    # Helpers for scope-specific use cases
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, tb):
        self.finish()

    def json(self):
        """Format as a dictionary of the correct shape for sending to the Cloud
        Trace REST API as a JSON object"""
        j = {
            'kind': self.kind,
            'name': self.name,
            'spanId': self.id,
            'startTime': self.startTime.isoformat() + 'Z',
            'endTime': self.endTime.isoformat() + 'Z',
        }
        return j


class TraceContext(object):
    def __init__(self, sendTrace=True):
        """
        If sendTrace is False, it will rely on a later TraceContext to send trace data.
        No data will be sent if there is no other TraceContext for this request.
        """
        if hasattr(trace_context, 'request') and trace_context.request:
            self._tcontext = trace_context.request.headers.get('X-Cloud-Trace-Context', 'NNNN/NNNN;xxxxx')
            self._doTrace = ';o=1' in self._tcontext
        else:
            self._doTrace = False

        if self._doTrace:
            logging.info("Trace Context: {}".format(self._tcontext))

        self._sendTrace = sendTrace

    def __enter__(self):
        self.start()
        return self

    def start(self):
        if self._doTrace:
            if not hasattr(trace_context, '_open_contexts'):
                trace_context._open_contexts = 0
                trace_context.spans = []
            trace_context._open_contexts += 1

    def __exit__(self, exc_type, exc_value, traceback):
        self.finish()

    def finish(self):
        if self._doTrace:
            trace_context._open_contexts -= 1
            if trace_context._open_contexts == 0 and self._sendTrace:
                self.write()
                trace_context.spans = []

    def span(self, name=""):
        spn = Span(name, self._doTrace)
        if self._doTrace:
            trace_context.spans.append(spn)
        return spn

    def write(self):
        try:
            # Breakup our given cloud tracing context so we can get the flags out of it
            trace_id, root_span_id = self._tcontext.split(';')[0].split('/')

            # Grab our spans object as a json blob
            spans = [s.json() for s in trace_context.spans]

            # catch
            if len(spans) == 0:
                return

            for s in spans:
                s['parentSpanId'] = root_span_id

            projectId = app_identity.get_application_id()
            traces_body = {
                    'projectId': projectId,
                    'traceId': trace_id,
                    'spans': spans
            }
            body = {
                'traces': [traces_body]
            }

            deferred.defer(send_trace, projectId, body, _queue="api-track-call", _url='/_ah/queue/deferred_stackdriver_send_trace')
        except Exception, e:
            logging.warning("TraceContext.write() failed!")
            logging.exception(e)
