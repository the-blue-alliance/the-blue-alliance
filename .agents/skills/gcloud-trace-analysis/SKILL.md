---
name: gcloud-trace-analysis
description: >-
  Query, inspect, and analyze Google Cloud Trace data for App Engine services and APIs.
  Use when investigating request latencies, span bottlenecks, slow endpoints, cache hit rates,
  cold starts, or profiling production traffic in Google Cloud.
---

# Google Cloud Trace Analysis Runbook

This skill provides step-by-step procedures for querying and analyzing Google Cloud Trace data for The Blue Alliance (project `tbatv-prod-hrd`) and other Google App Engine services.

---

## 1. Authentication & Access Token Retrieval

To query the Cloud Trace REST API, obtain a valid OAuth2 bearer token:

```bash
TOKEN=$(gcloud auth print-access-token)
```

---

## 2. Cloud Trace API Overview

The Cloud Trace v1 API endpoint for querying traces is:
```http
GET https://cloudtrace.googleapis.com/v1/projects/{projectId}/traces
```

### Key Query Parameters
- `view=COMPLETE`: **Crucial** — without this, only trace IDs and root spans are returned. `COMPLETE` includes all child spans and labels.
- `pageSize=100`: Number of traces per page (max 100).
- `pageToken`: Token for pagination from `nextPageToken`.
- `filter`: Filter expression (see syntax below).
- `orderBy`:
  - `duration desc`: Retrieve slowest traces first (best for bottleneck analysis).
  - `start desc`: Retrieve most recent traces first.
  - `start asc`: Retrieve chronological traces from a start window.

---

## 3. Filter Syntax (Cloud Trace v1)

| Goal | Filter Expression | Notes |
| :--- | :--- | :--- |
| **By GAE Service/Module** | `g.co/gae/app/module:py3-api` | Matches requests handled by the API service |
| **By Web Service** | `g.co/gae/app/module:py3-web` | Matches requests handled by the web frontend |
| **By Tasks Service** | `g.co/gae/app/module:py3-tasks-io` | Matches async queue / background tasks |
| **By Span Name Prefix** | `span:api_authenticated` | Matches traces containing a span starting with prefix |
| **By Root Span Prefix** | `root:/api/v3` | Matches root request URL/path prefix |
| **Combined Filter** | `g.co/gae/app/module:py3-api span:validate_keys` | Space-separated filters act as AND conditions |

---

## 4. Key Span Types & Interpretation

When parsing spans within a trace:

1. **Root Span (`/http/url`)**:
   - Contains `/http/status_code`, `/http/method`, `/http/response/size`, and GAE module/version labels.
2. **Front Overhead (Cold Start / Queuing)**:
   - Calculate: `first_child_span.startTime - root_span.startTime`.
   - Overhead > 500 ms indicates instance provisioning, cold start, or gunicorn queue delays.
3. **App Engine Built-in RPC Spans**:
   - `/memcache.Get`, `/memcache.Set`, `/memcache.Delete`: Memcache round trips.
   - `/datastore_v3.Get`, `/datastore_v3.Put`, `/datastore_v3.RunQuery`: Cloud Datastore operations.
   - `/taskqueue.BulkAdd`: Cloud Tasks / TaskQueue job scheduling.
4. **Application Spans**:
   - `api_authenticated`: Time verifying auth keys.
   - `validate_keys`: Time validating key format and entity existence.
   - `*.fetch_dict_async`: Query execution and dict serialization.
   - `profiled_jsonify`: JSON response serialization.
   - `Running AfterResponseMiddleware`: Teardown and deferred tasklet resolution.

---

## 5. Console Links

To provide clickable links to specific traces in the Google Cloud Console:
```text
https://console.cloud.google.com/traces/traces?project=tbatv-prod-hrd&tid={traceId}
```

---

## 6. Quick Python Extraction Recipe

Use this standard Python script to pull and parse a sample of traces:

```python
import json
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime

TOKEN = sys.argv[1]
PROJECT_ID = "tbatv-prod-hrd"
ctx = ssl._create_unverified_context()

def get_traces(filter_query, order_by="duration desc", count=10):
    params = {
        "pageSize": min(count, 100),
        "view": "COMPLETE",
        "filter": filter_query,
        "orderBy": order_by,
    }
    url = f"https://cloudtrace.googleapis.com/v1/projects/{PROJECT_ID}/traces?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode()).get("traces", [])

traces = get_traces("g.co/gae/app/module:py3-api", order_by="duration desc", count=5)
for t in traces:
    root = next((s for s in t.get("spans", []) if s.get("labels", {}).get("/http/url")), None)
    if root:
        r_start = datetime.fromisoformat(root["startTime"].rstrip("Z"))
        r_end = datetime.fromisoformat(root["endTime"].rstrip("Z"))
        dur = (r_end - r_start).total_seconds() * 1000
        url = root["labels"].get("/http/url")
        status = root["labels"].get("/http/status_code")
        print(f"{dur:6.1f}ms | {status} | {url}")
```
