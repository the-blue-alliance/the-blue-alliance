import json

from flask import abort, redirect, request, url_for
from google.appengine.ext import ndb
from pyre_extensions import safe_json
from werkzeug import Response

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.manipulators.award_manipulator import AwardManipulator
from backend.common.models.award import Award
from backend.common.models.award_recipient import AwardRecipient
from backend.common.models.event import Event
from backend.common.models.keys import AwardKey
from backend.common.models.team import Team
from backend.web.profiled_render import render_template


def award_dashboard() -> str:
    award_count = Award.query().count()
    template_values = {
        "award_count": award_count,
    }
    return render_template("admin/award_dashboard.html", template_values)


def award_delete_post() -> Response:
    award = Award.get_by_id(request.form["award_key"])
    if award is None:
        abort(404)

    AwardManipulator.delete(award)
    return redirect(url_for("admin.award_dashboard"))


def award_edit(award_key: AwardKey) -> str:
    award = Award.get_by_id(award_key)
    if award is None:
        abort(404)

    template_values = {
        "award": award,
    }
    return render_template("admin/award_edit.html", template_values)


def award_edit_post(award_key: AwardKey) -> Response:
    event_key_name = request.form["event_key_name"]
    award_type_enum = request.form["award_type_enum"]
    award_type = AwardType(int(award_type_enum))
    if award_key != Award.render_key_name(event_key_name, award_type):
        abort(400)

    recipient_json_list = []
    team_list = []
    for recipient in json.loads(request.form["recipient_list_json"]):
        safe_json.validate(recipient, AwardRecipient)
        recipient_json_list.append(json.dumps(recipient))
        if recipient["team_number"] is not None:
            team_list.append(ndb.Key(Team, "frc{}".format(recipient["team_number"])))

    event_type = EventType(int(request.form["event_type_enum"]))
    award = Award(
        id=award_key,
        name_str=request.form["name_str"],
        award_type_enum=award_type.value,
        event=ndb.Key(Event, event_key_name),
        event_type_enum=event_type.value,
        team_list=team_list,
        recipient_json_list=recipient_json_list,
    )

    AwardManipulator.createOrUpdate(award, auto_union=False)
    return redirect(url_for("admin.event_detail", event_key=event_key_name))
