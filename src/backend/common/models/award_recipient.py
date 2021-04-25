from typing import Optional, Union

from typing_extensions import TypedDict


class AwardRecipient(TypedDict):
    awardee: Optional[str]
    team_number: Optional[Union[int, str]]  # Ex: 7332 or 7332B
