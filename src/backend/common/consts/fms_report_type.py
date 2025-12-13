import enum

from backend.common.consts.auth_type import AuthType
from backend.common.consts.string_enum import StrEnum


@enum.unique
class FMSReportType(StrEnum):
    QUAL_RANKINGS = "qual_rankings"
    QUAL_SCHEDULE = "qual_schedule"
    QUAL_RESULTS = "qual_results"
    PLAYOFF_ALLIANCES = "playoff_alliances"
    PLAYOFF_SCHEDULE = "playoff_schedule"
    PLAYOFF_RESULTS = "playoff_results"
    TEAM_LIST = "team_list"


REQUIRED_REPORT_PERMISSOINS = {
    FMSReportType.QUAL_RANKINGS: AuthType.EVENT_RANKINGS,
    FMSReportType.QUAL_SCHEDULE: AuthType.EVENT_MATCHES,
    FMSReportType.QUAL_RESULTS: AuthType.EVENT_MATCHES,
    FMSReportType.PLAYOFF_ALLIANCES: AuthType.EVENT_ALLIANCES,
    FMSReportType.PLAYOFF_SCHEDULE: AuthType.EVENT_MATCHES,
    FMSReportType.PLAYOFF_RESULTS: AuthType.EVENT_MATCHES,
    FMSReportType.TEAM_LIST: AuthType.EVENT_TEAMS,
}
