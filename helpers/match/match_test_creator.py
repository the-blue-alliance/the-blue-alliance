import datetime
import json
import random

from helpers.match_manipulator import MatchManipulator
from models.match import Match


class MatchTestCreator(object):

    def __init__(self, event):
        self.event = event
        self.event.prepTeams()

    def buildTestMatch(self, comp_level, set_number, match_number, complete):
        teams = random.sample(self.event.teams, 6)
        youtube_videos = []
        tba_videos = []
        if complete:
            red_score = random.randint(0, 100)
            blue_score = random.randint(0, 100)
            if random.choice([True, False]):
                youtube_videos.append("P3C2BOtL7e8")
            if random.choice([True, False]):
                youtube_videos.append("TqY324xLU4s")
            if random.choice([True, False]):
                tba_videos.append('mp4')
        else:
            red_score = -1
            blue_score = -1

        alliances = {
            "red": {
                "teams": [team.key_name for team in teams[:3]],
                "score": red_score
            },
            "blue": {
                "teams": [team.key_name for team in teams[3:]],
                "score": blue_score
            }
        }

        if comp_level == "qm":
            id_string = "{}_{}{}".format(
                self.event.key_name,
                comp_level,
                match_number)
        else:
            id_string = "{}_{}{}m{}".format(
                self.event.key_name,
                comp_level,
                set_number,
                match_number)

        return Match(
            id=id_string,
            alliances_json=json.dumps(alliances),
            comp_level=comp_level,
            event=self.event.key,
            year=datetime.datetime.now().year,
            set_number=set_number,
            match_number=match_number,
            team_key_names=[team.key_name for team in teams],
            youtube_videos=youtube_videos,
            tba_videos=tba_videos,
            time=datetime.datetime.now() + datetime.timedelta(hours=2) + datetime.timedelta(minutes=6) * match_number
        )

    def createCompleteQuals(self):
        comp_level = "qm"
        set_number = 1
        complete = True
        matches = [self.buildTestMatch(comp_level, set_number, match_number, complete) for match_number in range(1, 11)]
        MatchManipulator.createOrUpdate(matches)

    def createIncompleteQuals(self):
        comp_level = "qm"
        set_number = 1
        complete = False
        matches = [self.buildTestMatch(comp_level, set_number, match_number, complete) for match_number in range(11, 21)]
        MatchManipulator.createOrUpdate(matches)
