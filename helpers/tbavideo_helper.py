import logging

from google.appengine.ext import db

from models import TBAVideo

class TBAVideoHelper(object):
    TBA_NET_VID_PATTERN = "http://videos.thebluealliance.com/%s/%s.%s"
    
    THUMBNAIL_FILETYPES = ["jpg", "jpeg"]
    STREAMABLE_FILETYPES = ["mp4", "flv"]
    DOWNLOADABLE_FILETYPES = ["mp4", "mov", "avi", "wmv", "flv"]
    
    def __init__(self, match):
        self.match = match
    
    def getThumbnailPath(self):
        return self._getBestPathOf(self.THUMBNAIL_FILETYPES)

    def getStreamablePath(self):
        return self._getBestPathOf(self.STREAMABLE_FILETYPES)
    
    def getDownloadablePath(self):
        return self._getBestPathOf(self.DOWNLOADABLE_FILETYPES)

    def _getBestPathOf(self, consider_filetypes):
        for filetype in consider_filetypes:
            if filetype in self.match.tba_videos:
                return self.TBA_NET_VID_PATTERN % (self.match.event_key_name(), self.match.get_key_name(), filetype)
        return None

class TBAVideoUpdater(object):
    """
    Helper class to handle TBAVideo objects when we are not sure whether they
    already exist or not.
    
    THIS CLASS IS DEPRECATED -gregmarra 31 Mar 2012
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
        Check if an tbavideo currently exists in the database based on match
        Doesn't put objects.
        If it does, update it and give it back.
        If it does not, give it back.
        """
        query = TBAVideo.all()
        
        # Look for a collision.
        tbavideo = TBAVideo.all().filter("match =", new_tbavideo.match).get()
        if tbavideo is not None:
            tbavideo = self.updateMerge(new_tbavideo, tbavideo)
            return tbavideo
        else:
            return new_tbavideo
    
    @classmethod
    def updateMerge(self, new_tbavideo, old_tbavideo):
        """
        Given an "old" and a "new" TBAVideo object, replace the fields in the
        "old" that are present in the "new".
        """
        
        old_tbavideo.filetypes = new_tbavideo.filetypes
        return old_tbavideo

