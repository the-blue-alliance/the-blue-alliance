from typing import NotRequired, TypedDict

from pyre_extensions import safe_json

from backend.common.consts.award_type import AWARD_TYPES, AwardType
from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.helpers.award_helper import AwardHelper
from backend.common.models.award import Award
from backend.common.models.award_recipient import AwardRecipient
from backend.common.models.keys import AwardKey, EventKey, TeamKey
from backend.common.models.team import Team


class AwardInfoInput(TypedDict):
    name_str: str
    type_enum: NotRequired[AwardType | None]
    team_key: NotRequired[TeamKey | None]
    awardee: NotRequired[str | None]


class AwardInfoParsed(TypedDict):
    name_str: str
    award_type_enum: AwardType
    team_key_list: list[TeamKey]
    recipient_list: list[AwardRecipient]


class JSONAwardsParser:
    @staticmethod
    def parse[
        T: (str, bytes)
    ](awards_json: T, event_key: EventKey) -> list[AwardInfoParsed]:  # fmt: skip
        """
        Parse JSON that contains a list of awards where each award is a dict of:
        name_str: String of award name. ex: "Tournament Winner" or "Dean's List Finalist"
        type_enum: Int of the award type enum. e.g. 2 for "Tournament Finalist". Can be null - will attempt to be matched by name.
        team_key: String in the format "frcXXX" for the team that won the award. Can be null.
        awardee: String corresponding to the name of an individual that won the award. Can be null.
        """
        # pyre validation doesn't support non-total TypedDict
        awards = safe_json.loads(awards_json, list[AwardInfoInput], validate=False)

        if not isinstance(awards, list):
            raise ParserInputException("Invalid JSON. Please check input.")

        awards_by_key: dict[AwardKey, AwardInfoParsed] = {}
        for award in awards:
            if not isinstance(award, dict):
                raise ParserInputException("Award must be a dict.")

            name_str = award.get("name_str")
            award_type_enum = award.get("type_enum")
            team_key = award.get("team_key")
            awardee = award.get("awardee")

            if not name_str:
                raise ParserInputException("Award must have a 'name_str'")

            if team_key and not Team.validate_key_name(team_key):
                raise ParserInputException(
                    f"Bad team_key: '{team_key}'. Must follow format 'frcXXX' or be null."
                )

            team_number = int(team_key[3:]) if team_key else None

            if award_type_enum not in AWARD_TYPES:
                # Fall back to name string parsing if award type enum is not valid
                award_type_enum = AwardHelper.parse_award_type(name_str)

            if award_type_enum is None:
                raise ParserInputException(
                    f"Cannot determine award type from: '{name_str}'."
                )

            if not team_key and not awardee:
                raise ParserInputException("One of team_key or awardee must be set!")

            recipient = AwardRecipient(
                team_number=team_number,
                awardee=awardee,
            )

            award_key = Award.render_key_name(event_key, award_type_enum)
            award_info = awards_by_key.setdefault(
                award_key,
                AwardInfoParsed(
                    name_str=name_str,
                    award_type_enum=award_type_enum,
                    team_key_list=[],
                    recipient_list=[],
                ),
            )
            if team_key:
                award_info["team_key_list"].append(team_key)
            award_info["recipient_list"].append(recipient)

        return list(awards_by_key.values())
