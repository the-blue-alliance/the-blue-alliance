from dataclasses import dataclass
from typing import List


@dataclass
class FMSSeason:
    """ Season information from the FMS API """
    event_count: int
    game_name: str
    kickoff: datetime
    rookie_start: int
    team_count: int
    frc_championships: List[FMSSeasonChampionship]


@dataclass
class FMSSeasonChampionship:
    """ Season CMP information from the FMS API """
    name: str
    start_date: str
    location: str
