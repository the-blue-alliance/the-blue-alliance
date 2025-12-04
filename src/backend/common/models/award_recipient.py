from typing import TypedDict


class AwardRecipient(TypedDict):
    awardee: str | None
    team_number: int | str | None  # Ex: 7332 or 7332B
