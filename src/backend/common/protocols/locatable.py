from typing import Protocol

from backend.common.models.location import Location


class Locatable(Protocol):
    city: str | None
    state_prov: str | None
    country: str | None
    postalcode: str | None

    @property
    def nl(self) -> Location | None:
        """Geocoded location. Events may have one; teams never do."""
        ...
