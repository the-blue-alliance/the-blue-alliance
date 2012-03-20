import logging

from google.appengine.ext import db

from models import YoutubeVideo

class YoutubeVideoUpdater(object):
    """
    Helper class to handle YoutubeVideo objects when we are not sure whether they
    already exist or not.
    DEPRECATED, since the YoutubeVideo class is deprecated.
    """
    
    @classmethod
    def createOrUpdate(self, new_youtubevideo):
        """
        Take an YoutubeVideo object, and either update the YoutubeVideo it is a newer
        version of, or create the YoutubeVideo if it is totally new.
        """
        youtubevideo = self.findOrSpawn(new_youtubevideo)
        youtubevideo.put()
        return youtubevideo
    
    @classmethod
    def findOrSpawn(self, new_youtubevideo):
        """"
        Check if an youtubevideo currently exists in the database based on key
        Doesn't put objects.
        If it does, update it and give it back.
        If it does not, give it back.
        """
        if new_youtubevideo.has_key():
          youtubevideo = YoutubeVideo.get_by_key_name(new_youtubevideo.key().name())
          youtubevideo = self.updateMerge(new_youtubevideo, youtubevideo)
          return youtubevideo
        else:
          return new_youtubevideo
    
    @classmethod
    def updateMerge(self, new_youtubevideo, old_youtubevideo):
        """
        Given an "old" and a "new" YoutubeVideo object, replace the fields in the
        "old" that are present in the "new".
        """
        
        old_youtubevideo.match = new_youtubevideo.match
        old_youtubevideo.youtube_id = new_youtubevideo.youtube_id
        return old_youtubevideo

