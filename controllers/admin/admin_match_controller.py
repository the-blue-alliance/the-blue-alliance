import json
import logging
import os

from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from models.event import Event
from models.match import Match
from helpers.match_manipulator import MatchManipulator

class AdminMatchCleanup(webapp.RequestHandler):
    """
    Given an Event, clean up all Matches that don't have the Event's key as their key prefix.
    Used to clean up 2011 Matches, where we had dupes of "2011new_qm1" and "2011newton_qm1".
    """
    def get(self):
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/matches_cleanup.html')
        self.response.out.write(template.render(path, {}))
    
    def post(self):
        event = Event.get_by_id(self.request.get("event_key_name"))
        matches_to_delete = list()
        match_keys_to_delete = list()
        if event is not None:
            for match in Match.query(Match.event == event.key):
                if match.key.id() != match.key_name:
                    matches_to_delete.append(match)
                    match_keys_to_delete.append(match.key_name)
            
            ndb.delete_multi(matches_to_delete)
        
        template_values = {
            "match_keys_deleted": match_keys_to_delete,
            "tried_delete": True
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/matches_cleanup.html')
        self.response.out.write(template.render(path, template_values))

class AdminMatchDashboard(webapp.RequestHandler):
    """
    Show stats about Matches
    """
    def get(self):
        match_count = Match.query().count()
        
        template_values = {
            "match_count": match_count
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/match_dashboard.html')
        self.response.out.write(template.render(path, template_values))
        

class AdminMatchDetail(webapp.RequestHandler):
    """
    Show a Match.
    """
    def get(self, match_key):
        match = Match.get_by_id(match_key)
        
        template_values = {
            "match": match
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/match_details.html')
        self.response.out.write(template.render(path, template_values))


class AdminMatchEdit(webapp.RequestHandler):
    """
    Edit a Match.
    """
    def get(self, match_key):
        match = Match.get_by_id(match_key)
        
        template_values = {
            "match": match
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/match_edit.html')
        self.response.out.write(template.render(path, template_values))
    
    def post(self, match_key):        
        alliances_json = self.request.get("alliances_json")
        alliances = json.loads(alliances_json)
        team_key_names = list()
        
        for alliance in alliances:
            team_key_names.extend(alliances[alliance].get('teams', None))
        
        match = Match(
            id = match_key,
            event = Event.get_by_id(self.request.get("event_key_name")).key,
            game = self.request.get("game"),
            set_number = int(self.request.get("set_number")),
            match_number = int(self.request.get("match_number")),
            comp_level = self.request.get("comp_level"),
            team_key_names = team_key_names,
            alliances_json = alliances_json,
            #no_auto_update = str(self.request.get("no_auto_update")).lower() == "true", #TODO
        )
        match = MatchManipulator.createOrUpdate(match)
        
        self.redirect("/admin/match/" + match.key_name)

class AdminVideosAdd(webapp.RequestHandler):
    """
    Add a lot of youtube_videos to Matches at once.
    """
    def get(self):
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/videos_add.html')
        self.response.out.write(template.render(path, {}))
        
    def post(self):
        logging.info(self.request)
        
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
        ndb.put_multi(matches_to_put)

        # TODO use Manipulators -gregmarra 20121006
        
        template_values = {
            "results": results,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/videos_add.html')
        self.response.out.write(template.render(path, template_values))