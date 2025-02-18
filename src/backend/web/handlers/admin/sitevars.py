from typing import Optional

from flask import redirect, request, url_for
from werkzeug.wrappers import Response

from backend.common.models.sitevar import Sitevar
from backend.web.profiled_render import render_template


def sitevars_list() -> str:
    sitevars = Sitevar.query().fetch(10000)

    template_values = {
        "sitevars": sitevars,
    }

    return render_template("admin/sitevar_list.html", template_values)


def sitevar_edit(sitevar_key: str) -> str:
    sitevar = Sitevar.get_by_id(sitevar_key)

    success = request.args.get("success")

    template_values = {
        "sitevar": sitevar,
        "success": success,
    }

    return render_template("admin/sitevar_edit.html", template_values)


def sitevar_edit_post(sitevar_key: Optional[str] = None) -> Response:
    # note, we don't use sitevar_key

    sitevar = Sitevar(
        id=request.form.get("key"),
        description=request.form.get("description"),
        values_json=request.form.get("values_json"),
    )
    sitevar.put()

    return redirect(
        url_for("admin.sitevar_edit", sitevar_key=sitevar.key.id(), success="true")
    )


def sitevar_create() -> str:
    return render_template("admin/sitevar_create.html")
