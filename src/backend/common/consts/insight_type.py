import enum

from backend.common.consts.string_enum import StrEnum


@enum.unique
class InsightType(StrEnum):
    MATCHES = "matches"
    AWARDS = "awards"
    PREDICTIONS = "predictions"
    DISTRICTS = "districts"
