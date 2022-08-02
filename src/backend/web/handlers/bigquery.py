from datetime import timedelta

from flask import redirect
from werkzeug.wrappers.response import Response

from backend.common.decorators import cached_public


@cached_public(ttl=timedelta(weeks=1))
def bigquery() -> Response:
    return redirect(
        "https://console.cloud.google.com/bigquery?project=tbatv-prod-hrd&p=tbatv-prod-hrd&d=the_blue_alliance&page=dataset"
    )
