from backend.common.decorators import cached_public
from backend.web.profiled_render import render_template


@cached_public(timeout=int(60 * 60 * 24 * 7))
def apidocs_trusted_v1() -> str:
    template_values = {
        "title": "Trusted APIv1",
        "swagger_url": "/swagger/api_trusted_v1.json",
    }
    return render_template("apidocs_swagger.html", template_values)


@cached_public(timeout=int(60 * 60 * 24 * 7))
def apidocs_v3() -> str:
    template_values = {
        "title": "APIv3",
        "swagger_url": "/swagger/api_v3.json",
    }
    return render_template("apidocs_swagger.html", template_values)
