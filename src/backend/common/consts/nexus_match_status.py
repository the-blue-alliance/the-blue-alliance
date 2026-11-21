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
        return NEXUS_MATCH_STATUS_STRINGS[self]


# Defined outside the enum body so it isn't treated as a member. Every member
# must have an entry, which nexus_match_status_test checks.
NEXUS_MATCH_STATUS_STRINGS: dict[NexusMatchStatus, str] = {
    NexusMatchStatus.QUEUING_SOON: "Queuing soon",
    NexusMatchStatus.NOW_QUEUING: "Now queuing",
    NexusMatchStatus.ON_DECK: "On deck",
    NexusMatchStatus.ON_FIELD: "On field",
}
