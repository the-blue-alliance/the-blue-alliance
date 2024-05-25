from typing import Optional, TypedDict, Union


class AwardRecipient(TypedDict):
    awardee: Optional[str]
    team_number: Optional[Union[int, str]]  # Ex: 7332 or 7332B
