import re
from typing import AnyStr, Dict, List, TypedDict

from pyre_extensions import safe_json

from backend.common.consts.award_type import AWARD_TYPES, AwardType
from backend.common.datafeed_parsers.exceptions import ParserInputException
from backend.common.helpers.award_helper import AwardHelper
from backend.common.models.award import Award
from backend.common.models.award_recipient import AwardRecipient
from backend.common.models.keys import AwardKey, EventKey, TeamKey


class AwardInfoInput(TypedDict, total=False):
    name_str: str
    team_key: str
    awardee: str


class AwardInfoParsed(TypedDict):
    name_str: str
    award_type_enum: AwardType
    team_key_list: List[TeamKey]
    recipient_list: List[AwardRecipient]


class JSONAwardsParser:
    @classmethod
    def parse(self, awards_json: AnyStr, event_key: EventKey) -> List[AwardInfoParsed]:
        """
        Parse JSON that contains a list of awards where each award is a dict of:
        award_type_enum: Int of the award type enum. e.g. 2 for "Tournament Finalist"
        name_str: String of award name. ex: "Tournament Winner" or "Dean's List Finalist"
        team_key: String in the format "frcXXX" for the team that won the award. Can be null.
        awardee: String corresponding to the name of an individual that won the award. Can be null.
        """
        awards = safe_json.loads(awards_json, List[AwardInfoParsed], validate=False)

        awards_by_key: Dict[AwardKey, AwardInfoParsed] = {}
        for award in awards:
            award_type_enum = award.get("type_enum", None)
            name_str = award.get("name_str", None)
            team_key = award.get("team_key", None)
            awardee = award.get("awardee", None)

            if name_str is None:
                raise ParserInputException("Award must have a 'name_str'")

            if team_key and not re.match(r"frc\d+", str(team_key)):
                raise ParserInputException(
                    f"Bad team_key: '{team_key}'. Must follow format 'frcXXX' or be null."
                )

            if award_type_enum not in AWARD_TYPES:
                # Fall back to name string parsing if award type enum is not valid
                award_type_enum = AwardHelper.parse_award_type(name_str)
                if award_type_enum is None:
                    raise ParserInputException(
                        f"Cannot determine award type from: '{name_str}'. Please contact a www.thebluealliance.com admin."
                    )

            if not team_key and not awardee:
                raise ParserInputException("One of team_key or awardee must be set!")

            recipient = AwardRecipient(
                team_number=(
                    (int(team_key[3:]) if team_key[3:].isdigit() else team_key[3:])
                    if team_key
                    else None
                ),
                awardee=awardee,
            )

            award_key_name = Award.render_key_name(event_key, award_type_enum)
            if award_key_name in awards_by_key:
                if team_key is not None:
                    awards_by_key[award_key_name]["team_key_list"].append(team_key)
                awards_by_key[award_key_name]["recipient_list"].append(recipient)
            else:
                awards_by_key[award_key_name] = AwardInfoParsed(
                    name_str=name_str,
                    award_type_enum=award_type_enum,
                    team_key_list=[team_key] if team_key else [],
                    recipient_list=[recipient],
                )

        return list(awards_by_key.values())
