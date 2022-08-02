from datetime import timedelta

from flask import redirect
from werkzeug.wrappers.response import Response

from backend.common.decorators import cached_public


@cached_public(ttl=timedelta(weeks=1))
def swag() -> Response:
    return redirect(
        "https://www.amazon.com/s/ref=w_bl_sl_s_ap_web_7141123011?ie=UTF8&node=7141123011&field-brandtextbin=The+Blue+Alliance"
    )
