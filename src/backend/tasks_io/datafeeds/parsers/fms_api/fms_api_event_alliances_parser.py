from typing import List

from backend.common.frc_api.types import AllianceListModelV2, AllianceModelV2
from backend.common.models.alliance import EventAlliance, EventAllianceBackup
from backend.tasks_io.datafeeds.parsers.parser_base import ParserBase


class FMSAPIEventAlliancesParser(ParserBase[AllianceListModelV2, List[EventAlliance]]):
    def parse(self, response: AllianceListModelV2) -> List[EventAlliance]:
        alliances = []

        alliance_response: list[AllianceModelV2] = response["Alliances"] or []
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
            if api_name := alliance["name"]:
                name = api_name
            else:
                name = "Alliance {}".format(alliance_number)

            if api_backup := alliance["backup"]:
                backup_replaced = "frc{}".format(api_backup)
            else:
                backup_replaced = None

            if api_backup_replaced := alliance["backupReplaced"]:
                backup_replacement = "frc{}".format(api_backup_replaced)
            else:
                backup_replacement = None

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

        return alliances
