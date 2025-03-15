from backend.common.consts.string_enum import StrEnum


class NexusMatchStatus(StrEnum):
    QUEUEING_SOON = "Queuing soon"
    NOW_QUEUEING = "Now queuing"
    ON_DECK = "On deck"
    ON_FIELD = "On field"
