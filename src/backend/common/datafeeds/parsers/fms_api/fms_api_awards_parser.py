import json
from typing import Any, Dict, List, Optional

from google.cloud import ndb

from backend.common.datafeeds.parsers.json.parser_json import ParserJSON
from backend.common.helpers.award_helper import AwardHelper
from backend.common.models.award import Award
from backend.common.models.event import Event
from backend.common.models.team import Team


class FMSAPIAwardsParser(ParserJSON[List[Award]]):
    def __init__(
        self, event: Event, valid_team_nums: Optional[List[int]] = None
    ) -> None:
        self.event = event
        self.valid_team_nums = valid_team_nums

    def parse(self, response: Dict[str, Any]) -> Optional[List[Award]]:
        awards_by_type = {}
        for award in response["Awards"]:
            team_number = award["teamNumber"]

            valid_team_nums = self.valid_team_nums
            if valid_team_nums is not None and team_number not in valid_team_nums:
                continue

            award_type_enum = AwardHelper.parse_award_type(award["name"])
            if award_type_enum is None:
                continue

            recipient_json = json.dumps(
                {
                    "team_number": team_number,
                    "awardee": award["person"],
                }
            )

            if award_type_enum in awards_by_type:
                if team_number is not None:
                    awards_by_type[award_type_enum]["team_number_list"].append(
                        team_number
                    )
                awards_by_type[award_type_enum]["recipient_json_list"].append(
                    recipient_json
                )
            else:
                awards_by_type[award_type_enum] = {
                    "name_str": award["name"],
                    "award_type_enum": award_type_enum,
                    "team_number_list": [team_number]
                    if team_number is not None
                    else [],
                    "recipient_json_list": [recipient_json],
                }

        awards = []
        for award in awards_by_type.values():
            awards.append(
                Award(
                    id=Award.render_key_name(
                        self.event.key_name, award["award_type_enum"]
                    ),
                    name_str=award["name_str"],
                    award_type_enum=award["award_type_enum"],
                    year=self.event.year,
                    event=self.event.key,
                    event_type_enum=self.event.event_type_enum,
                    team_list=[
                        ndb.Key(Team, "frc{}".format(team_number))
                        for team_number in award["team_number_list"]
                    ],
                    recipient_json_list=award["recipient_json_list"],
                )
            )

        return awards if awards else None
