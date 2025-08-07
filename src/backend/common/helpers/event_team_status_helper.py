import copy
from collections import defaultdict
from typing import cast, List, Optional, Set, Tuple

from pyre_extensions import none_throws

from backend.common.consts.alliance_color import ALLIANCE_COLORS
from backend.common.consts.comp_level import (
    CompLevel,
    ELIM_LEVELS,
)
from backend.common.consts.playoff_type import (
    DoubleElimRound,
    ORDERED_DOUBLE_ELIM_ROUNDS,
    PlayoffType,
)
from backend.common.helpers.alliance_helper import AllianceHelper
from backend.common.helpers.match_helper import MatchHelper, TOrganizedMatches
from backend.common.helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from backend.common.helpers.rankings_helper import RankingsHelper
from backend.common.models.alliance import (
    EventAlliance,
    PlayoffAllianceStatus,
    PlayoffOutcome,
)
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_team_status import (
    EventTeamLevelStatus,
    EventTeamRanking,
    EventTeamStatus,
    EventTeamStatusAlliance,
    EventTeamStatusQual,
    WLTRecord,
)
from backend.common.models.keys import TeamKey, Year
from backend.common.models.match import Match


class EventTeamStatusHelper:
    @classmethod
    def generate_team_at_event_alliance_status_string(
        cls, team_key: TeamKey, status_dict: EventTeamStatus
    ) -> str:
        if not status_dict:
            return "--"
        alliance = status_dict.get("alliance")
        if alliance:
            pick = alliance["pick"]
            if pick == 0:
                pick = "Captain"
            else:
                # Convert to ordinal number http://stackoverflow.com/questions/9647202/ordinal-numbers-replacement
                pick = "{} Pick".format(
                    "%d%s"
                    % (
                        pick,
                        "tsnrhtdd"[
                            (pick / 10 % 10 != 1) * (pick % 10 < 4) * pick % 10 :: 4
                        ],
                    )
                )
            backup = alliance["backup"]
            if backup and team_key == backup["in"]:
                pick = "Backup"

            return "<b>{}</b> of <b>{}</b>".format(pick, alliance["name"])
        else:
            return "--"

    @classmethod
    def generate_team_at_event_playoff_status_string(
        cls, team_key: TeamKey, status_dict: EventTeamStatus
    ) -> str:
        if not status_dict:
            return "--"
        playoff = status_dict.get("playoff")
        if playoff:
            level = playoff["level"]
            status = playoff.get("status")
            record = playoff.get("record")
            playoff_average = playoff.get("playoff_average")
            playoff_type = playoff.get("playoff_type")

            level_str = AllianceHelper.generate_playoff_level_status_string(
                playoff_type, playoff
            )

            if status == PlayoffOutcome.PLAYING:
                level_record = none_throws(playoff["current_level_record"])
                record_str = "{}-{}-{}".format(
                    level_record["wins"], level_record["losses"], level_record["ties"]
                )
                playoff_str = "Currently <b>{}</b> in the <b>{}</b>".format(
                    record_str, level_str
                )
            else:
                if status == PlayoffOutcome.WON:
                    if level == CompLevel.F:
                        playoff_str = "<b>Won the event</b>"
                    else:
                        playoff_str = "<b>Won the {}</b>".format(level_str)
                elif status == PlayoffOutcome.ELIMINATED:
                    playoff_str = "<b>Eliminated in the {}</b>".format(level_str)
                else:
                    raise Exception("Unknown playoff status: {}".format(status))
                if record:
                    playoff_str += " with a playoff record of <b>{}-{}-{}</b>".format(
                        record["wins"], record["losses"], record["ties"]
                    )
                if playoff_average:
                    playoff_str += " with a playoff average of <b>{:.1f}</b>".format(
                        playoff_average
                    )
            return playoff_str
        else:
            return "--"

    @classmethod
    def generate_team_at_event_status_string(
        cls,
        team_key: TeamKey,
        status_dict: EventTeamStatus,
        formatting: bool = True,
        event: Optional[Event] = None,
        include_team: bool = True,
        verbose: bool = False,
    ) -> str:
        """
        Generate a team at event status string from a status dict
        """
        if include_team:
            default_msg = "Team {} is waiting for the {} to begin.".format(
                team_key[3:], event.normalized_name if event else "event"
            )
        else:
            default_msg = "is waiting for the {} to begin.".format(
                event.normalized_name if event else "event"
            )
        if not status_dict:
            return default_msg

        qual = status_dict.get("qual")
        alliance = status_dict.get("alliance")
        playoff = status_dict.get("playoff")

        components = []
        if qual:
            status = qual.get("status")
            num_teams = qual.get("num_teams")
            ranking = qual.get("ranking")

            if ranking:
                rank = ranking.get("rank")
                record = ranking.get("record")
                qual_average = ranking.get("qual_average")

                num_teams_str = ""
                if num_teams:
                    num_teams_str = (
                        " of {}".format(num_teams)
                        if verbose
                        else "/{}".format(num_teams)
                    )

                if status == EventTeamLevelStatus.COMPLETED:
                    is_tense = "was"
                    has_tense = "had"
                else:
                    is_tense = "is"
                    has_tense = "has"

                qual_str = None
                if record:
                    if verbose:
                        record_str = cls._build_verbose_record(record)
                    else:
                        record_str = "{}-{}-{}".format(
                            record["wins"], record["losses"], record["ties"]
                        )
                    if rank:
                        qual_str = "{} <b>Rank {}{}</b> with a record of <b>{}</b> in quals".format(
                            is_tense, rank, num_teams_str, record_str
                        )
                    else:
                        qual_str = "{} a record of <b>{}</b> in quals".format(
                            has_tense, record_str
                        )
                elif qual_average:
                    if rank:
                        qual_str = "{} <b>Rank {}{}</b> with an average score of <b>{:.1f}</b> in quals".format(
                            is_tense, rank, num_teams_str, qual_average
                        )
                    else:
                        qual_str = (
                            "{} an average score of <b>{:.1f}</b> in quals".format(
                                has_tense, qual_average
                            )
                        )

                if qual_str:
                    components.append(qual_str)

        pick = None
        if alliance:
            pick = alliance["pick"]
            if pick == 0:
                pick = "Captain"
            else:
                pick = AllianceHelper.get_ordinal_pick_from_number(pick)
            backup = alliance["backup"]
            if backup and team_key == backup["in"]:
                pick = "Backup"

            if not playoff:
                alliance_str = "will be competing in the playoffs as the <b>{}</b> of <b>{}</b>".format(
                    pick, alliance["name"]
                )
                components.append(alliance_str)

        if playoff:
            alliance_name = alliance.get("name") if alliance else None
            if playoff["status"] == PlayoffOutcome.PLAYING:
                components = AllianceHelper.generate_playoff_status_string(
                    playoff, pick, alliance_name
                )
            else:
                components.extend(
                    AllianceHelper.generate_playoff_status_string(
                        playoff, pick, alliance_name
                    )
                )

        if not components:
            return default_msg

        if len(components) > 1:
            components[-1] = "and {}".format(components[-1])
        if len(components) > 2:
            join_str = ", "
        else:
            join_str = " "

        if include_team:
            final_string = "Team {} {}".format(team_key[3:], join_str.join(components))
        else:
            final_string = "{}".format(join_str.join(components))
        if event:
            final_string += " at the {}.".format(event.normalized_name)
        else:
            final_string += "."
        return (
            final_string
            if formatting
            else final_string.replace("<b>", "").replace("</b>", "")
        )

    @classmethod
    def generate_team_at_event_status(
        cls, team_key: TeamKey, event: Event, match_list: Optional[List[Match]] = None
    ) -> EventTeamStatus:
        """
        Generate a dict containing team@event status information
        :param team_key: Key name of the team to focus on
        :param event: Event object
        :param matches: Organized matches (via MatchHelper.organized_matches) from the event, optional
        """
        event_details = event.details
        if not match_list:
            match_list = event.matches
        team_matches = [m for m in match_list if team_key in m.team_key_names]
        next_match = MatchHelper.upcoming_matches(team_matches, num=1)
        last_match = MatchHelper.recent_matches(team_matches, num=1)
        matches = MatchHelper.organized_matches(match_list)[1]
        status = EventTeamStatus(
            qual=cls._build_qual_info(team_key, event_details, matches, event.year),
            alliance=cls._build_alliance_info(team_key, event_details, matches),
            playoff=cls._build_playoff_info(
                team_key, event_details, matches, event.year, event.playoff_type
            ),
            last_match_key=last_match[0].key_name if last_match else None,
            next_match_key=next_match[0].key_name if next_match else None,
        )

        # TODO: Results are getting mixed unless copied. 2017-02-03 -fangeugene
        return copy.deepcopy(status)

    @classmethod
    def _build_qual_info(
        cls,
        team_key: TeamKey,
        event_details: Optional[EventDetails],
        matches: TOrganizedMatches,
        year: Year,
    ) -> Optional[EventTeamStatusQual]:
        if not matches[CompLevel.QM]:
            status = EventTeamLevelStatus.NOT_STARTED
        else:
            status = EventTeamLevelStatus.COMPLETED
            for match in matches[CompLevel.QM]:
                if not match.has_been_played:
                    status = EventTeamLevelStatus.PLAYING
                    break

        if event_details and event_details.rankings2:
            rankings = event_details.rankings2

            qual_info: Optional[EventTeamStatusQual] = None
            for ranking in rankings:
                if ranking["team_key"] == team_key:
                    qual_info = {
                        "status": status,
                        "ranking": cast(EventTeamRanking, ranking),
                        "num_teams": 0,
                        "sort_order_info": None,
                    }
                    break

            if qual_info:
                qual_info["num_teams"] = len(rankings)
                qual_info["sort_order_info"] = (
                    RankingsHelper.get_sort_order_info(event_details) or []
                )

            return qual_info
        else:
            # Use matches as fallback
            all_teams = set()
            wins = 0
            losses = 0
            ties = 0
            qual_score_sum = 0
            matches_played = 0
            for match in matches[CompLevel.QM]:
                for color in ALLIANCE_COLORS:
                    for team in match.alliances[color]["teams"]:
                        all_teams.add(team)
                        if (
                            team == team_key
                            and match.has_been_played
                            and team_key not in match.alliances[color]["surrogates"]
                        ):
                            matches_played += 1

                            if match.winning_alliance == color:
                                wins += 1
                            elif match.winning_alliance == "":
                                ties += 1
                            else:
                                losses += 1

                            qual_score_sum += match.alliances[color]["score"]

            qual_average = (
                float(qual_score_sum) / matches_played if matches_played else 0
            )

            if team_key in all_teams:
                return {
                    "status": status,
                    "ranking": {
                        "rank": None,
                        "matches_played": matches_played,
                        "dq": None,
                        "record": (
                            WLTRecord(
                                wins=wins,
                                losses=losses,
                                ties=ties,
                            )
                            if year != 2015
                            else None
                        ),
                        "qual_average": qual_average if year == 2015 else None,
                        "sort_orders": None,
                        "team_key": team_key,
                    },
                    "num_teams": len(all_teams),
                    "sort_order_info": None,
                }
            else:
                return None

    @classmethod
    def _build_alliance_info(
        cls,
        team_key: TeamKey,
        event_details: Optional[EventDetails],
        matches: TOrganizedMatches,
    ) -> Optional[EventTeamStatusAlliance]:
        if not event_details or not event_details.alliance_selections:
            return None
        alliance, number = cls._get_alliance(team_key, event_details, matches)
        if not alliance:
            return None

        # Calculate the role played by the team on the alliance
        backup_info = alliance.get("backup", {}) if alliance.get("backup") else {}
        pick = -1 if team_key == backup_info.get("in", "") else None
        for i, team in enumerate(alliance["picks"]):
            if team == team_key:
                pick = i
                break

        return {
            "pick": none_throws(pick),
            "name": alliance.get("name", "Alliance {}".format(number)),
            "number": number or -1,
            "backup": alliance.get("backup"),
        }

    @classmethod
    def _build_playoff_info(
        cls,
        team_key: TeamKey,
        event_details: Optional[EventDetails],
        matches: TOrganizedMatches,
        year: Year,
        playoff_type: PlayoffType,
    ) -> Optional[PlayoffAllianceStatus]:
        alliance, _ = cls._get_alliance(team_key, event_details, matches)
        complete_alliance = set(alliance["picks"]) if alliance else set()
        if alliance and alliance.get("backup"):
            complete_alliance.add(alliance["backup"]["in"])

        if playoff_type == PlayoffType.AVG_SCORE_8_TEAM:
            # 2015 tournament; the bracket function handles its special cases as well
            return cls._build_playoff_info_bracket(
                complete_alliance, matches, year, playoff_type
            )

        elif playoff_type == PlayoffType.ROUND_ROBIN_6_TEAM:
            # Some years' CMP playoffs
            return cls._build_playoff_info_round_robin(
                complete_alliance,
                matches,
                year,
                playoff_type,
                event_details.alliance_selections if event_details else None,
            )

        elif playoff_type in [
            PlayoffType.DOUBLE_ELIM_4_TEAM,
            PlayoffType.DOUBLE_ELIM_8_TEAM,
        ]:
            # The standard playoff for 2023 and on
            return cls._build_playoff_info_double_elim(
                complete_alliance, matches, year, playoff_type
            )

        else:
            # Otherwise, default to a best-of-N bracket
            return cls._build_playoff_info_bracket(
                complete_alliance, matches, year, playoff_type
            )

    @classmethod
    def _build_playoff_info_bracket(
        cls,
        complete_alliance: Set[TeamKey],
        matches: TOrganizedMatches,
        year: Year,
        playoff_type: PlayoffType,
    ) -> Optional[PlayoffAllianceStatus]:
        # Matches needs to be all playoff matches at the event, to properly account for backups
        import numpy as np

        is_bo5 = playoff_type == PlayoffType.BO5_FINALS

        all_wins = 0
        all_losses = 0
        all_ties = 0
        playoff_scores = []
        status: Optional[PlayoffAllianceStatus] = None
        for comp_level in reversed(ELIM_LEVELS):  # playoffs
            if matches[comp_level]:
                level_wins = 0
                level_losses = 0
                level_ties = 0
                level_matches = 0
                level_played = 0
                for match in matches[comp_level]:
                    for color in ALLIANCE_COLORS:
                        match_alliance = set(match.alliances[color]["teams"])
                        if len(match_alliance.intersection(complete_alliance)) >= 2:
                            playoff_scores.append(match.alliances[color]["score"])
                            level_matches += 1
                            if match.has_been_played:
                                if match.winning_alliance == color:
                                    level_wins += 1
                                    all_wins += 1
                                elif not match.winning_alliance:
                                    if not (year == 2015 and comp_level != CompLevel.F):
                                        # The match was a tie
                                        level_ties += 1
                                        all_ties += 1
                                else:
                                    level_losses += 1
                                    all_losses += 1
                                level_played += 1
                if not status:
                    # Only set this for the first comp level that gets this far,
                    # But run through the rest to calculate the full record
                    if level_wins == (3 if is_bo5 else 2):
                        status = {
                            "playoff_type": playoff_type,
                            "status": PlayoffOutcome.WON,
                            "level": comp_level,
                            "current_level_record": None,
                            "record": None,
                            "playoff_average": None,
                        }
                    elif level_losses == (3 if is_bo5 else 2):
                        status = {
                            "playoff_type": playoff_type,
                            "status": PlayoffOutcome.ELIMINATED,
                            "level": comp_level,
                            "current_level_record": None,
                            "record": None,
                            "playoff_average": None,
                        }
                    elif level_matches > 0:
                        if year == 2015:
                            # This only works for past events, but 2015 is in the past so this works
                            status = {
                                "playoff_type": playoff_type,
                                "status": PlayoffOutcome.ELIMINATED,
                                "level": comp_level,
                                "current_level_record": None,
                                "record": None,
                                "playoff_average": None,
                            }
                        else:
                            status = {
                                "playoff_type": playoff_type,
                                "status": PlayoffOutcome.PLAYING,
                                "level": comp_level,
                                "current_level_record": None,
                                "record": None,
                                "playoff_average": None,
                            }
                    if status:
                        status["current_level_record"] = (
                            WLTRecord(
                                wins=level_wins,
                                losses=level_losses,
                                ties=level_ties,
                            )
                            if year != 2015 or comp_level == CompLevel.F
                            else None
                        )

        if status:
            status["record"] = (
                WLTRecord(wins=all_wins, losses=all_losses, ties=all_ties)
                if year != 2015
                else None
            )
            status["playoff_average"] = (
                np.mean(playoff_scores) if year == 2015 else None
            )
        return status

    @classmethod
    def _build_playoff_info_double_elim(
        cls,
        complete_alliance: Set[TeamKey],
        matches: TOrganizedMatches,
        year: Year,
        playoff_type: PlayoffType,
    ) -> Optional[PlayoffAllianceStatus]:
        if playoff_type == PlayoffType.DOUBLE_ELIM_8_TEAM:
            double_elim_matches = MatchHelper.organized_double_elim_matches(
                matches, year
            )
        elif playoff_type == PlayoffType.DOUBLE_ELIM_4_TEAM:
            double_elim_matches = MatchHelper.organized_double_elim_4_matches(matches)
        else:
            return None

        overall_record = WLTRecord(wins=0, losses=0, ties=0)
        double_elim_record = WLTRecord(wins=0, losses=0, ties=0)
        finals_record = WLTRecord(wins=0, losses=0, ties=0)

        round_records: defaultdict[DoubleElimRound, WLTRecord] = defaultdict(
            lambda: WLTRecord(wins=0, losses=0, ties=0)
        )
        rounds_played: Set[DoubleElimRound] = set()
        for round in reversed(ORDERED_DOUBLE_ELIM_ROUNDS):
            for match in double_elim_matches[round]:
                for color in ALLIANCE_COLORS:
                    match_alliance = set(match.alliances[color]["teams"])
                    if len(match_alliance.intersection(complete_alliance)) >= 2:
                        rounds_played.add(round)

                        PlayoffAdvancementHelper.update_wlt(
                            match, color, overall_record
                        )
                        PlayoffAdvancementHelper.update_wlt(
                            match, color, round_records[round]
                        )

                        if round == DoubleElimRound.FINALS:
                            PlayoffAdvancementHelper.update_wlt(
                                match, color, finals_record
                            )
                        else:
                            PlayoffAdvancementHelper.update_wlt(
                                match, color, double_elim_record
                            )

        latest_round = next(
            (r for r in reversed(ORDERED_DOUBLE_ELIM_ROUNDS) if r in rounds_played),
            None,
        )
        latest_level = (
            CompLevel.F if latest_round == DoubleElimRound.FINALS else CompLevel.SF
        )
        current_record = (
            finals_record
            if latest_round == DoubleElimRound.FINALS
            else double_elim_record
        )

        if latest_round == DoubleElimRound.FINALS and finals_record["wins"] == 2:
            # Event winner -- won two finals matches
            return {
                "playoff_type": playoff_type,
                "status": PlayoffOutcome.WON,
                "level": latest_level,
                "double_elim_round": latest_round,
                "current_level_record": current_record,
                "record": overall_record,
            }

        if double_elim_record["losses"] >= 2 or finals_record["losses"] >= 2:
            # Eliminated if two double elim or finals losses
            return {
                "playoff_type": playoff_type,
                "status": PlayoffOutcome.ELIMINATED,
                "level": latest_level,
                "double_elim_round": latest_round,
                "current_level_record": current_record,
                "record": overall_record,
            }

        elif rounds_played:
            # Everybody else, still playing, as long as they have
            # at least one match on the schedule
            return {
                "playoff_type": playoff_type,
                "status": PlayoffOutcome.PLAYING,
                "level": latest_level,
                "double_elim_round": latest_round,
                "current_level_record": current_record,
                "record": overall_record,
            }

        else:
            # Lastly, the team had no playoff matches scheduled,
            # so they were unpicked
            return None

    @classmethod
    def _build_playoff_info_round_robin(
        cls,
        complete_alliance: Set[TeamKey],
        matches: TOrganizedMatches,
        year: Year,
        playoff_type: PlayoffType,
        alliance_selections: Optional[List[EventAlliance]],
    ) -> Optional[PlayoffAllianceStatus]:
        round_robin_rank = None
        round_robin_record = WLTRecord(wins=0, losses=0, ties=0)
        finals_record = WLTRecord(wins=0, losses=0, ties=0)
        has_finals_match = False

        round_robin_advancement = (
            PlayoffAdvancementHelper.generate_playoff_advancement_round_robin(
                matches, year, alliance_selections
            )
        )
        for i, advancement in enumerate(round_robin_advancement["sf"]):
            if (
                len(
                    {f"frc{t}" for t in advancement.complete_alliance}.intersection(
                        complete_alliance
                    )
                )
                >= 2
            ):
                round_robin_rank = i + 1
                round_robin_record = advancement.record

        for comp_level in [CompLevel.F]:
            if not matches.get(comp_level):
                continue

            for match in matches[comp_level]:
                for color in ALLIANCE_COLORS:
                    match_alliance = set(match.alliances[color]["teams"])
                    if len(match_alliance.intersection(complete_alliance)) >= 2:
                        if match.comp_level == CompLevel.F:
                            has_finals_match = True
                            PlayoffAdvancementHelper.update_wlt(
                                match, color, finals_record
                            )

        overall_record = WLTRecord(
            wins=round_robin_record["wins"] + finals_record["wins"],
            losses=round_robin_record["losses"] + finals_record["losses"],
            ties=round_robin_record["ties"] + finals_record["ties"],
        )

        if has_finals_match and finals_record["wins"] >= 2:
            # Event winners (2+ wins in the final best-of-3)
            return {
                "playoff_type": playoff_type,
                "status": PlayoffOutcome.WON,
                "level": CompLevel.F,
                "current_level_record": finals_record,
                "record": overall_record,
                "round_robin_rank": round_robin_rank,
                "advanced_to_round_robin_finals": True,
            }

        elif has_finals_match and finals_record["losses"] >= 2:
            # Event finalist (2+ losses in the final best-of-3)
            return {
                "playoff_type": playoff_type,
                "status": PlayoffOutcome.ELIMINATED,
                "level": CompLevel.F,
                "current_level_record": finals_record,
                "record": overall_record,
                "round_robin_rank": round_robin_rank,
                "advanced_to_round_robin_finals": True,
            }

        elif (
            round_robin_rank is not None
            and round_robin_advancement["sf_complete"]
            and not has_finals_match
        ):
            # Eliminated in the round robin tournament
            return {
                "playoff_type": playoff_type,
                "status": PlayoffOutcome.ELIMINATED,
                "level": CompLevel.SF,
                "current_level_record": round_robin_record,
                "record": overall_record,
                "round_robin_rank": round_robin_rank,
                "advanced_to_round_robin_finals": False,
            }

        elif round_robin_rank is not None:
            # Still playing, if we found round robin data for them
            return {
                "playoff_type": playoff_type,
                "status": PlayoffOutcome.PLAYING,
                "level": CompLevel.F if has_finals_match else CompLevel.SF,
                "current_level_record": (
                    finals_record if has_finals_match else round_robin_record
                ),
                "record": overall_record,
                "round_robin_rank": round_robin_rank,
                "advanced_to_round_robin_finals": has_finals_match,
            }

        else:
            # Otherwise, the team did not participant in playoffs
            return None

    @classmethod
    def _get_alliance(
        cls,
        team_key: TeamKey,
        event_details: Optional[EventDetails],
        matches: TOrganizedMatches,
    ) -> Tuple[
        Optional[EventAlliance], Optional[int]
    ]:  # Tuple of (Alliance, Alliance Number)
        """
        Get the alliance number of the team
        Returns 0 when the team is not on an alliance
        """
        if event_details and event_details.alliance_selections:
            for i, alliance in enumerate(event_details.alliance_selections):
                alliance_number = i + 1
                if team_key in alliance["picks"]:
                    return alliance, alliance_number

                backup_info = alliance.get("backup") or {}
                if team_key == backup_info.get("in", ""):
                    # If this team came in as a backup team
                    return alliance, alliance_number
        else:
            # No event_details. Use matches to generate alliances.
            complete_alliances = []
            for comp_level in ELIM_LEVELS:
                for match in matches[comp_level]:
                    for color in ALLIANCE_COLORS:
                        alliance = copy.copy(match.alliances[color]["teams"])
                        for i, complete_alliance in enumerate(
                            complete_alliances
                        ):  # search for alliance. could be more efficient
                            if (
                                len(set(alliance).intersection(set(complete_alliance)))
                                >= 2
                            ):  # if >= 2 teams are the same, then the alliance is the same
                                backups = list(
                                    set(alliance).difference(set(complete_alliance))
                                )
                                complete_alliances[
                                    i
                                ] += backups  # ensures that backup robots are listed last
                                break
                        else:
                            complete_alliances.append(alliance)

            for complete_alliance in complete_alliances:
                if team_key in complete_alliance:
                    return {
                        "picks": complete_alliance
                    }, None  # Alliance number is unknown

        alliance_number = 0
        return None, alliance_number  # Team didn't make it to elims

    @classmethod
    def _build_verbose_record(cls, record: WLTRecord) -> str:
        win_label = "wins" if record["wins"] != 1 else "win"
        loss_label = "losses" if record["losses"] != 1 else "loss"
        tie_label = "ties" if record["ties"] != 1 else "tie"
        return "{} {}, {} {}, and {} {}".format(
            record["wins"],
            win_label,
            record["losses"],
            loss_label,
            record["ties"],
            tie_label,
        )
