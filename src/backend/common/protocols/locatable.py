from typing import Protocol

from backend.common.models.location import Location


class Locatable(Protocol):
    city: str | None
    state_prov: str | None
    country: str | None
    postalcode: str | None
    nl: Location | None
