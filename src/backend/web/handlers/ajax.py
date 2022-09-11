from flask import jsonify, make_response, Response

from backend.common.decorators import cached_public
from backend.common.models.typeahead_entry import TypeaheadEntry


@cached_public
def typeahead_handler(search_key: str) -> Response:
    entry = TypeaheadEntry.get_by_id(search_key)
    if entry is None:
        return jsonify([])

    response = make_response(entry.data_json)
    response.content_type = 'application/json; charset="utf-8"'
    response.last_modified = entry.updated
    return response
