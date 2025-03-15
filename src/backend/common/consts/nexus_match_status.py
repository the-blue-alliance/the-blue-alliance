import enum


@enum.unique
class NexusMatchStatus(enum.IntEnum):
    QUEUING_SOON = 1
    NOW_QUEUING = 2
    ON_DECK = 3
    ON_FIELD = 4

    @classmethod
    def from_string(cls, name: str) -> "NexusMatchStatus":
        match name:
            case "Queuing soon":
                return cls.QUEUING_SOON
            case "Now queuing":
                return cls.NOW_QUEUING
            case "On deck":
                return cls.ON_DECK
            case "On field":
                return cls.ON_FIELD
        raise ValueError(f"Unknown value for NexusMatchStatus: {name}")

    def to_string(self) -> str:
        match self:
            case self.QUEUING_SOON:
                return "Queuing soon"
            case self.NOW_QUEUING:
                return "Now queuing"
            case self.ON_DECK:
                return "On deck"
            case self.ON_FIELD:
                return "On field"

        raise ValueError(f"Unknown value for NexusMatchStatus: {self}")
