import os
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from models import YoutubeVideo, Match
from helpers.youtubevideo_helper import YoutubeVideoUpdater

class AdminYoutubeVideoEdit(webapp.RequestHandler):
    """
    Edit a YoutubeVideo.
    """
    def get(self, youtubevideo_key):
        youtubevideo = YoutubeVideo.get_by_id(int(youtubevideo_key))
        
        template_values = {
            "youtubevideo": youtubevideo
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/youtubevideos/edit.html')
        self.response.out.write(template.render(path, template_values))
    
    def post(self, youtubevideo_key):
        
        if (self.request.get("submit") == "Save"):
          match = Match.get_by_key_name(self.request.get("match_key_name"))
          
          youtubevideo = YoutubeVideo(
              key_name = youtubevideo_key,
              match = match,
              youtube_id = self.request.get("youtube_id")
          )
          youtubevideo = YoutubeVideoUpdater.createOrUpdate(youtubevideo)
          self.redirect("/admin/youtubevideo/edit/" + youtubevideo.key().id_or_name())
        elif (self.request.get("delete") == "Delete"):
          youtubevideo = YoutubeVideo.get_by_id(youtubevideo_key)
          youtubevideo.delete()
          self.redirect("/admin/match/" + self.request.get("match_key_name"))
        else:
          self.redirect("/admin/youtubevideos/edit/" + youtubevideo_key)


class AdminYoutubeVideoAdd(webapp.RequestHandler):
    """
    Add a YoutubeVideo.
    """
    def get(self):
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/youtubevideos/add.html')
        template_values = {}
        self.response.out.write(template.render(path, template_values))

    def post(self):
        youtubevideo = YoutubeVideo(
            match = Match.get_by_key_name(self.request.get("match_key_name")),
            youtube_id = self.request.get("youtube_id")
        )
        youtubevideo = YoutubeVideoUpdater.createOrUpdate(youtubevideo)
        self.redirect("/admin/youtubevideos/edit/" + str(youtubevideo.key().id_or_name()))
        
