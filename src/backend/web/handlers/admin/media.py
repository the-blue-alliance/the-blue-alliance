from flask import abort, redirect, request
from werkzeug import Response

from backend.common.manipulators.media_manipulator import MediaManipulator
from backend.common.models.media import Media
from backend.common.suggestions.media_parser import MediaParser
from backend.web.profiled_render import render_template


def media_dashboard() -> str:
    media_count = Media.query().count()

    template_values = {
        "media_count": media_count,
    }
    return render_template("admin/media_dashboard.html", template_values)


def media_delete_reference(media_key_name: str) -> Response:
    media = Media.get_by_id(media_key_name)
    if media is None:
        abort(404)

    reference_type = request.form["reference_type"]
    reference_key_name = request.form["reference_key_name"]
    media_reference = media.create_reference(reference_type, reference_key_name)
    media.references.remove(media_reference)
    MediaManipulator.createOrUpdate(media, auto_union=False)

    redirect_url = request.form["originating_url"]
    return redirect(redirect_url)


def media_make_preferred(media_key_name: str) -> Response:
    media = Media.get_by_id(media_key_name)
    if media is None:
        abort(404)

    reference_type = request.form["reference_type"]
    reference_key_name = request.form["reference_key_name"]
    media_reference = media.create_reference(reference_type, reference_key_name)
    media.preferred_references.append(media_reference)
    MediaManipulator.createOrUpdate(media)

    redirect_url = request.form["originating_url"]
    return redirect(redirect_url)


def media_remove_preferred(media_key_name: str) -> Response:
    media = Media.get_by_id(media_key_name)
    if media is None:
        abort(404)

    reference_type = request.form["reference_type"]
    reference_key_name = request.form["reference_key_name"]
    media_reference = media.create_reference(reference_type, reference_key_name)
    media.preferred_references.remove(media_reference)
    MediaManipulator.createOrUpdate(media, auto_union=False)

    redirect_url = request.form["originating_url"]
    return redirect(redirect_url)


def media_add() -> Response:
    media_url = request.form["media_url"].strip()
    media_dict = MediaParser.partial_media_dict_from_url(media_url)
    if media_dict is None:
        abort(400)

    year_str = request.form.get("year")
    if not year_str:
        year = None
    else:
        year = int(year_str)

    reference_type = request.form["reference_type"]
    reference_key_name = request.form["reference_key"]
    media_reference = Media.create_reference(reference_type, reference_key_name)
    media = Media(
        id=Media.render_key_name(
            media_dict["media_type_enum"], media_dict["foreign_key"]
        ),
        foreign_key=media_dict["foreign_key"],
        media_type_enum=media_dict["media_type_enum"],
        details_json=media_dict.get("details_json", None),
        year=year,
        references=[media_reference],
    )
    MediaManipulator.createOrUpdate(media)

    redirect_url = request.form["originating_url"]
    return redirect(redirect_url)
