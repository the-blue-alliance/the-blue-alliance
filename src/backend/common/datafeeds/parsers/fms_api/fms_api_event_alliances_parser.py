from typing import Any, Dict, List, Optional

from backend.common.datafeeds.parsers.parser_json import ParserJSON
from backend.common.models.alliance import EventAlliance, EventAllianceBackup


class FMSAPIEventAlliancesParser(ParserJSON[Optional[List[EventAlliance]]]):
    def parse(self, response: Dict[str, Any]) -> Optional[List[EventAlliance]]:
        alliances = []

        alliance_response = response["Alliances"]
        for i in range(len(alliance_response)):
            alliance = alliance_response[i]
            alliance_number = i + 1

            picks = []
            if alliance["captain"] is not None:
                picks.append("frc{}".format(alliance["captain"]))
            if alliance["round1"] is not None:
                picks.append("frc{}".format(alliance["round1"]))
            if alliance["round2"] is not None:
                picks.append("frc{}".format(alliance["round2"]))
            if alliance["round3"] is not None:
                picks.append("frc{}".format(alliance["round3"]))

            # If there are no picks for a given alliance, ignore this alliance
            if len(picks) == 0:
                continue

            # If no name is specified (like in 2015), generate one
            name = (
                alliance["name"]
                if alliance.get("name", None)
                else "Alliance {}".format(alliance_number)
            )

            backup_replaced = (
                "frc{}".format(alliance["backup"])
                if alliance.get("backup", None)
                else None
            )
            backup_replacement = (
                "frc{}".format(alliance["backupReplaced"])
                if alliance.get("backupReplaced", None)
                else None
            )

            if backup_replaced and backup_replacement:
                backup: EventAllianceBackup = {
                    "in": backup_replaced,
                    "out": backup_replacement,
                }
                alliances.append(
                    EventAlliance(picks=picks, declines=[], name=name, backup=backup)
                )
            else:
                alliances.append(EventAlliance(picks=picks, declines=[], name=name))

        return alliances if alliances else None
