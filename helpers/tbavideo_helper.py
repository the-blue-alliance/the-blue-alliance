import logging

class TBAVideoHelper(object):
    """
    Same interface as the retired TBAVideo class.
    """
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
