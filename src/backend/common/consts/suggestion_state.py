import enum


@enum.unique
class SuggestionState(enum.IntEnum):
    REVIEW_ACCEPTED = 1
    REVIEW_PENDING = 0
    REVIEW_REJECTED = -1
    REVIEW_AUTOREJECTED = -2
