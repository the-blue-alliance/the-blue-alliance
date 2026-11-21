from backend.common.models.typeahead_entry import TypeaheadEntry


def test_typeahead_entry_round_trip(ndb_stub) -> None:
    TypeaheadEntry(id=TypeaheadEntry.ALL_TEAMS_KEY, data_json="[]").put()

    entry = TypeaheadEntry.get_by_id("teams-all")
    assert entry is not None
    assert entry.data_json == "[]"
    assert TypeaheadEntry.YEAR_EVENTS_KEY.format(2019) == "events-2019"
