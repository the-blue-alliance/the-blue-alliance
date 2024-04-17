import datetime
from collections import defaultdict

from google.appengine.ext import ndb
from werkzeug.wrappers import Response

from backend.common.consts.award_type import AwardType
from backend.common.consts.event_type import EventType
from backend.common.helpers.event_helper import EventHelper
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.team_helper import TeamHelper
from backend.common.models.event import Event
from backend.common.models.keys import TeamKey
from backend.common.models.team import Team
from backend.common.queries.award_query import TeamEventTypeAwardsQuery
from backend.common.queries.event_details_query import EventDetailsQuery
from backend.common.queries.event_query import TeamYearEventTeamsQuery
from backend.web.decorators import require_login
from backend.web.profiled_render import render_template


def get_qual_bluezone_score(prediction):
    redScore = prediction["red"]["score"]
    blueScore = prediction["blue"]["score"]
    winningScore = redScore if redScore > blueScore else blueScore
    losingScore = redScore if redScore < blueScore else blueScore
    scorePower = min(
        float(winningScore + 2 * losingScore) / (200.0 * 3) * 50, 50
    )  # High score ~200, up to 50 BlueZone points
    skillPower = min(
        (
            min(prediction["red"]["note_scored"] / 21, 1)
            + min(prediction["blue"]["note_scored"] / 21, 1)
            + min(prediction["red"]["stage_points"] / 10, 1)
            + min(prediction["blue"]["stage_points"] / 10, 1)
        )
        * 50
        / 4,
        50,
    )  # Up to 50 BlueZone points

    return scorePower + skillPower


@ndb.tasklet
def fetch_team_details_async(team_key: TeamKey):
    team = yield Team.get_by_id_async(team_key)

    current_year = datetime.datetime.now().year
    event_teams = yield TeamYearEventTeamsQuery(
        team_key=team_key, year=current_year
    ).fetch_async()
    division_win_awards = yield TeamEventTypeAwardsQuery(
        team_key=team_key,
        event_type=EventType.CMP_DIVISION,
        award_type=AwardType.WINNER,
    ).fetch_async()

    events_details = []
    for event_team in event_teams:
        event_key = event_team.key.id().split("_")[0]
        event = yield Event.get_by_id_async(event_key)
        event_details = yield EventDetailsQuery(event_key).fetch_async()

        alliance = event_team.status["alliance"]["number"]
        pick = event_team.status["alliance"]["pick"]
        events_details.append(
            {
                "event_short": event.event_short,
                "name": event.name,
                "alliance": f"A{alliance}P{'C' if pick == 0 else pick}",
                "finish": f"{event_team.status['playoff']['double_elim_round']} ({event_team.status['playoff']['status']})",
                "auto_note_copr": event_details.coprs.get(
                    "Total Auto Game Pieces", {}
                ).get(team_key[3:]),
                "teleop_note_copr": event_details.coprs.get(
                    "Total Teleop Game Pieces", {}
                ).get(team_key[3:]),
                "trap_copr": event_details.coprs.get("Total Trap", {}).get(
                    team_key[3:]
                ),
            }
        )

    past_einstein = []
    for division_win_award in division_win_awards:
        past_einstein.append(division_win_award.year)

    return {
        "team": team,
        "past_einstein": past_einstein,
        "events": events_details,
    }


@require_login
def match_suggestion() -> Response:
    current_events = list(filter(lambda e: e.now, EventHelper.events_within_a_day()))
    popular_teams_events = TeamHelper.getPopularTeamsEvents(current_events)

    popular_team_keys = set()
    for team, _ in popular_teams_events:
        popular_team_keys.add(team.key.id())

    for event in current_events:
        event.prep_details()
        event.prep_matches()

    finished_matches = []
    current_matches = []
    upcoming_matches = []
    ranks = {}
    alliances = {}
    team_keys = set()
    for event in current_events:
        if not event.details:
            continue
        finished_matches += MatchHelper.recent_matches(event.matches, num=1)
        for i, match in enumerate(MatchHelper.upcoming_matches(event.matches, num=3)):
            if not match.time:
                continue

            for team_key in (
                match.alliances["red"]["teams"] + match.alliances["blue"]["teams"]
            ):
                team_keys.add(team_key)

            if (
                not event.details.predictions
                or match.key.id()
                not in event.details.predictions["match_predictions"][
                    "qual" if match.comp_level == "qm" else "playoff"
                ]
            ):
                # pyre-ignore[16]
                match.prediction = defaultdict(lambda: defaultdict(float))
                # pyre-ignore[16]
                match.bluezone_score = 0
            else:
                match.prediction = event.details.predictions["match_predictions"][
                    "qual" if match.comp_level == "qm" else "playoff"
                ][match.key.id()]
                match.bluezone_score = get_qual_bluezone_score(match.prediction)
            if i == 0:
                current_matches.append(match)
            else:
                upcoming_matches.append(match)
        if event.details.rankings2:
            for rank in event.details.rankings2:
                ranks[rank["team_key"]] = rank["rank"]
        if event.alliance_selections:
            for i, alliance in enumerate(event.alliance_selections):
                for pick in alliance["picks"]:
                    alliances[pick] = i + 1

    finished_matches = sorted(
        finished_matches, key=lambda m: m.actual_time if m.actual_time else m.time
    )
    current_matches = sorted(
        current_matches, key=lambda m: m.predicted_time if m.predicted_time else m.time
    )
    upcoming_matches = sorted(
        upcoming_matches, key=lambda m: m.predicted_time if m.predicted_time else m.time
    )

    team_detail_futures = [fetch_team_details_async(team_key) for team_key in team_keys]
    team_details = {}
    for detail_future in team_detail_futures:
        detail = detail_future.get_result()
        team_details[detail["team"].key.id()] = detail

    template_values = {
        "finished_matches": finished_matches,
        "current_matches": current_matches,
        "upcoming_matches": upcoming_matches,
        "ranks": ranks,
        "alliances": alliances,
        "popular_team_keys": popular_team_keys,
        "team_details": team_details,
    }

    return render_template("match_suggestion.html", template_values)
