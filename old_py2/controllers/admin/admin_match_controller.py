import json
import logging
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from datafeeds.offseason_matches_parser import OffseasonMatchesParser
from helpers.match_manipulator import MatchManipulator
from models.event import Event
from models.match import Match


class AdminMatchCleanup(LoggedInHandler):
    """
    Given an Event, clean up all Matches that don't have the Event's key as their key prefix.
    Used to clean up 2011 Matches, where we had dupes of "2011new_qm1" and "2011newton_qm1".
    """
    def get(self):
        self._require_admin()
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/matches_cleanup.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()
        event = Event.get_by_id(self.request.get("event_key_name"))
        matches_to_delete = list()
        match_keys_to_delete = list()
        if event is not None:
            for match in Match.query(Match.event == event.key):
                if match.key.id() != match.key_name:
                    matches_to_delete.append(match)
                    match_keys_to_delete.append(match.key_name)

            MatchManipulator.delete(matches_to_delete)

        self.template_values.update({
            "match_keys_deleted": match_keys_to_delete,
            "tried_delete": True
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/matches_cleanup.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminMatchDashboard(LoggedInHandler):
    """
    Show stats about Matches
    """
    def get(self):
        self._require_admin()

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/match_dashboard.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminMatchDelete(LoggedInHandler):
    """
    Delete a Match.
    """
    def get(self, event_key_id):
        self._require_admin()

        match = Match.get_by_id(event_key_id)

        self.template_values.update({
            "match": match
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/match_delete.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, match_key_id):
        self._require_admin()

        logging.warning("Deleting %s at the request of %s / %s" % (
            match_key_id,
            self.user_bundle.user.user_id(),
            self.user_bundle.user.email()))

        match = Match.get_by_id(match_key_id)
        event_key_id = match.event.id()

        MatchManipulator.delete(match)

        self.redirect("/admin/event/%s?deleted=%s" % (event_key_id, match_key_id))


class AdminMatchDetail(LoggedInHandler):
    """
    Show a Match.
    """
    def get(self, match_key):
        self._require_admin()
        match = Match.get_by_id(match_key)

        self.template_values.update({
            "match": match
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/match_details.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminMatchAdd(LoggedInHandler):
    """
    Add Matches from CSV.
    """
    def post(self):
        self._require_admin()
        event_key = self.request.get('event_key')
        matches_csv = self.request.get('matches_csv')
        matches, _ = OffseasonMatchesParser.parse(matches_csv)

        event = Event.get_by_id(event_key)
        matches = [Match(
            id=Match.renderKeyName(
                event.key.id(),
                match.get("comp_level", None),
                match.get("set_number", 0),
                match.get("match_number", 0)),
            event=event.key,
            year=event.year,
            set_number=match.get("set_number", 0),
            match_number=match.get("match_number", 0),
            comp_level=match.get("comp_level", None),
            team_key_names=match.get("team_key_names", None),
            alliances_json=match.get("alliances_json", None)
            )
            for match in matches]
        MatchManipulator.createOrUpdate(matches)

        self.redirect('/admin/event/{}'.format(event_key))


class AdminMatchEdit(LoggedInHandler):
    """
    Edit a Match.
    """
    def get(self, match_key):
        self._require_admin()
        match = Match.get_by_id(match_key)

        self.template_values.update({
            "match": match
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/match_edit.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, match_key):
        self._require_admin()
        alliances_json = self.request.get("alliances_json")
        score_breakdown_json = self.request.get("score_breakdown_json")
        alliances = json.loads(alliances_json)
        tba_videos = json.loads(self.request.get("tba_videos")) if self.request.get("tba_videos") else []
        youtube_videos = json.loads(self.request.get("youtube_videos")) if self.request.get("youtube_videos") else []
        team_key_names = list()

        for alliance in alliances:
            team_key_names.extend(alliances[alliance].get('teams', None))

        match = Match(
            id=match_key,
            event=Event.get_by_id(self.request.get("event_key_name")).key,
            set_number=int(self.request.get("set_number")),
            match_number=int(self.request.get("match_number")),
            comp_level=self.request.get("comp_level"),
            team_key_names=team_key_names,
            alliances_json=alliances_json,
            score_breakdown_json=score_breakdown_json,
            tba_videos=tba_videos,
            youtube_videos=youtube_videos
            # no_auto_update = str(self.request.get("no_auto_update")).lower() == "true", #TODO
        )
        MatchManipulator.createOrUpdate(match, auto_union=False)

        self.redirect("/admin/match/" + match.key_name)


class AdminVideosAdd(LoggedInHandler):
    """
    Add a lot of youtube_videos to Matches at once.
    """
    def get(self):
        self._require_admin()
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/videos_add.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self):
        self._require_admin()

        additions = json.loads(self.request.get("youtube_additions_json"))
        match_keys, youtube_videos = zip(*additions["videos"])
        matches = ndb.get_multi([ndb.Key(Match, match_key) for match_key in match_keys])

        matches_to_put = []
        results = {"existing": [], "bad_match": [], "added": []}
        for (match, match_key, youtube_video) in zip(matches, match_keys, youtube_videos):
            if match:
                if youtube_video not in match.youtube_videos:
                    match.youtube_videos.append(youtube_video)
                    matches_to_put.append(match)
                    results["added"].append(match_key)
                else:
                    results["existing"].append(match_key)
            else:
                results["bad_match"].append(match_key)

        MatchManipulator.createOrUpdate(matches_to_put)

        self.template_values.update({
            "results": results,
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/videos_add.html')
        self.response.out.write(template.render(path, self.template_values))
