from typing import Optional

from typing_extensions import TypedDict


class AwardRecipient(TypedDict):
    awardee: Optional[str]
    team_number: Optional[int]
