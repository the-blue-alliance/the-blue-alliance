from datetime import timedelta

from flask import redirect

from backend.common.decorators import cached_public


@cached_public(ttl=timedelta(seconds=61))
def bigquery() -> str:
    return redirect("https://console.cloud.google.com/bigquery?project=tbatv-prod-hrd&p=tbatv-prod-hrd&d=the_blue_alliance&page=dataset")
