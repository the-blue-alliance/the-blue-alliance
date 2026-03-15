from backend.common.models.event import Event


def stream_matches_event(title: str, description: str, event: Event) -> bool:
    """Returns True if the given stream title/description matches the given event.

    A stream is considered a match if the event's short name appears in the
    stream title or description, or if the upper-cased event code appears in
    the stream description.
    """
    if event.short_name:
        if event.short_name in title:
            return True
        if event.short_name in description:
            return True

    if event.event_short and event.event_short.upper() in description:
        return True

    return False
