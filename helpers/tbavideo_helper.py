import logging

from google.appengine.ext import db

from models import TBAVideo

class TBAVideoUpdater(object):
    """
    Helper class to handle TBAVideo objects when we are not sure whether they
    already exist or not.
    """
    
    @classmethod
    def createOrUpdate(self, new_tbavideo):
        """
        Take an TBAVideo object, and either update the TBAVideo it is a newer
        version of, or create the TBAVideo if it is totally new.
        """
        tbavideo = self.findOrSpawn(new_tbavideo)
        tbavideo.put()
        return tbavideo
    
    @classmethod
    def findOrSpawn(self, new_tbavideo):
        """"
        Check if an tbavideo currently exists in the database based on (match, filetype)
        Doesn't put objects.
        If it does, update it and give it back.
        If it does not, give it back.
        """
        query = TBAVideo.all()
        
        # Look for a collision.
        tbavideo = TBAVideo.all().filter("match =", new_tbavideo.match).filter("filetype =", new_tbavideo.filetype).get()
        if tbavideo is not None:
            tbavideo = self.updateMerge(new_tbavideo, tbavideo)
            return tbavideo
        else:
            return new_tbavideo
    
    @classmethod
    def updateMerge(self, new_tbavideo, old_tbavideo):
        """
        Given an "old" and a "new" TBAVideo object, replace the fields in the
        "old" team that are present in the "new" team.
        """
        
        old_tbavideo.url = new_tbavideo.url
        return old_tbavideo

