import datetime

from backend.common.models.event import Event
from backend.web.handlers.suggestions.suggest_apiwrite_review_controller import (
    compute_expiration,
    EXPIRATION_DAY_OFFSETS,
)

NOW = datetime.datetime(2026, 9, 4, 12, 0, 0)


def _event(end_date):
    return Event(
        id="2025test",
        event_short="test",
        year=2025,
        start_date=(end_date - datetime.timedelta(days=2)) if end_date else None,
        end_date=end_date,
    )


def test_expiration_is_relative_to_event_end_for_an_ongoing_event() -> None:
    """While an event is still running, the event-relative candidate wins.

    Note this only holds while the event ends *later* than now; for an event
    that finished even a day ago the now-relative candidate is already larger,
    because end_date is midnight while now has a time component.
    """
    event = _event(datetime.datetime(2026, 9, 6))  # ends 2 days after NOW

    expiration = compute_expiration(event, 7, NOW)

    # end_date is midnight at the start of the last day, hence the extra day.
    assert expiration == datetime.datetime(2026, 9, 14)
    assert expiration is not None and expiration > NOW + datetime.timedelta(days=7)


def test_key_granted_long_after_the_event_is_still_usable() -> None:
    """A 7-day key granted a year late must not arrive already expired.

    This is the whole reason compute_expiration takes a max() rather than
    keying off the event alone.
    """
    event = _event(datetime.datetime(2025, 9, 3))  # ~1 year before NOW

    expiration = compute_expiration(event, 7, NOW)

    assert expiration == NOW + datetime.timedelta(days=7)
    assert expiration is not None and expiration > NOW


def test_zero_day_key_granted_long_after_the_event_expires_immediately() -> None:
    """The 0-day option genuinely means 'right now' for a finished event."""
    event = _event(datetime.datetime(2025, 9, 3))

    assert compute_expiration(event, 0, NOW) == NOW


def test_negative_one_means_never_expires() -> None:
    event = _event(datetime.datetime(2025, 9, 3))

    assert compute_expiration(event, -1, NOW) is None


def test_event_without_an_end_date_falls_back_to_now() -> None:
    """Some offseason events have no dates; this used to raise TypeError."""
    event = _event(None)

    assert compute_expiration(event, 7, NOW) == NOW + datetime.timedelta(days=7)


def test_missing_event_falls_back_to_now() -> None:
    assert compute_expiration(None, 3, NOW) == NOW + datetime.timedelta(days=3)


def test_every_offered_offset_produces_a_future_expiration_for_a_past_event() -> None:
    """No option in the dropdown should hand out an already-dead key.

    0 is the deliberate exception -- it means "expire now".
    """
    event = _event(datetime.datetime(2025, 9, 3))

    for offset in EXPIRATION_DAY_OFFSETS:
        expiration = compute_expiration(event, offset, NOW)
        if offset == -1:
            assert expiration is None
        elif offset == 0:
            assert expiration == NOW
        else:
            assert (
                expiration is not None and expiration > NOW
            ), f"offset {offset} produced a dead key"


def _pending_apiwrite_suggestion(event_key: str, end_date) -> None:
    from google.appengine.ext import ndb

    from backend.common.consts.suggestion_state import SuggestionState
    from backend.common.models.account import Account
    from backend.common.models.suggestion import Suggestion
    from backend.common.models.suggestion_dict import SuggestionDict

    account = Account(id="reqester@example.com", email="requester@example.com")
    account.put()

    from backend.common.consts.event_type import EventType

    Event(
        id=event_key,
        event_short=event_key[4:],
        event_type_enum=EventType.OFFSEASON,
        year=int(event_key[:4]),
        name="Test Event",
        start_date=(end_date - datetime.timedelta(days=2)) if end_date else None,
        end_date=end_date,
    ).put()

    suggestion = Suggestion(
        author=ndb.Key(Account, "reqester@example.com"),
        review_state=SuggestionState.REVIEW_PENDING,
        target_model="api_auth_access",
    )
    suggestion.contents = SuggestionDict(
        event_key=event_key,
        affiliation="Volunteer",
        auth_types=[],
    )
    suggestion.put()


def test_review_page_shows_event_dates_and_computed_expirations(
    login_user, web_client
) -> None:
    """The page must render with the extra date data and surface it."""
    from backend.common.consts.account_permission import AccountPermission

    login_user.has_permission.return_value = True
    login_user.permissions = [AccountPermission.REVIEW_APIWRITE]

    _pending_apiwrite_suggestion("2026test", datetime.datetime(2026, 4, 10))

    resp = web_client.get("/suggest/apiwrite/review")

    assert resp.status_code == 200
    assert b"Event dates" in resp.data
    # Relative status renders (this event is in the past).
    assert b"ended" in resp.data and b"days ago" in resp.data
    # The dropdown labels the expiration each option would actually produce.
    assert b"expires" in resp.data
    assert b"never expires" in resp.data


def test_review_page_renders_for_an_event_with_no_dates(login_user, web_client) -> None:
    """Some offseason events have no dates; the page must not blow up."""
    from backend.common.consts.account_permission import AccountPermission

    login_user.has_permission.return_value = True
    login_user.permissions = [AccountPermission.REVIEW_APIWRITE]

    _pending_apiwrite_suggestion("2026nodate", None)

    resp = web_client.get("/suggest/apiwrite/review")

    assert resp.status_code == 200
    assert b"no dates on this event" in resp.data
