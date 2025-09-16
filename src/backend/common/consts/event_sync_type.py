from enum import IntFlag


class EventSyncType(IntFlag):
    EVENT_ALLIANCES = 1
    EVENT_RANKINGS = 2
    EVENT_QUAL_MATCHES = 4
    EVENT_PLAYOFF_MATCHES = 8
    EVENT_AWARDS = 16
