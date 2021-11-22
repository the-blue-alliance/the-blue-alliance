from dataclasses import dataclass


@dataclass
class FMSAPI:
    """ The index information for the FMS API """
    name: str
    api_version: str
    status: str
    current_season: int
    max_season: int
