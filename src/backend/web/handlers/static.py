from datetime import timedelta

from flask import redirect, render_template
from werkzeug.wrappers.response import Response

from backend.common.decorators import cached_public


@cached_public(ttl=timedelta(weeks=1))
def add_data() -> str:
    return render_template("add_data.html")


@cached_public(ttl=timedelta(weeks=1))
def brand() -> str:
    return render_template("brand.html")


@cached_public(ttl=timedelta(weeks=1))
def contact() -> str:
    return render_template("contact.html")


@cached_public(ttl=timedelta(weeks=1))
def bigquery() -> Response:
    return redirect(
        "https://console.cloud.google.com/bigquery?project=tbatv-prod-hrd&p=tbatv-prod-hrd&d=the_blue_alliance&page=dataset"
    )


@cached_public(ttl=timedelta(weeks=1))
def opr() -> str:
    return render_template("opr.html")


@cached_public(ttl=timedelta(weeks=1))
def privacy() -> str:
    return render_template("privacy.html")


@cached_public(ttl=timedelta(weeks=1))
def thanks() -> str:
    return render_template("thanks.html")


@cached_public(ttl=timedelta(weeks=1))
def donate() -> str:
    return render_template("donate.html")


@cached_public(ttl=timedelta(weeks=1))
def swag() -> Response:
    return redirect(
        "https://www.amazon.com/s/ref=w_bl_sl_s_ap_web_7141123011?ie=UTF8&node=7141123011&field-brandtextbin=The+Blue+Alliance"
    )
