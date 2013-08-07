class TBAVideoHelper(object):
    """
    Same interface as the retired TBAVideo class.
    """
    TBA_NET_VID_PATTERN = "http://videos.thebluealliance.net/%s/%s.%s"

    THUMBNAIL_FILETYPES = ["jpg", "jpeg"]
    STREAMABLE_FILETYPES = ["mp4", "flv"]
    DOWNLOADABLE_FILETYPES = ["mp4", "mov", "avi", "wmv", "flv"]

    def __init__(self, match):
        self.match = match

    @property
    def thumbnail_path(self):
        return self._best_path_of(self.THUMBNAIL_FILETYPES)

    @property
    def streamable_path(self):
        return self._best_path_of(self.STREAMABLE_FILETYPES)

    @property
    def downloadable_path(self):
        return self._best_path_of(self.DOWNLOADABLE_FILETYPES)

    def _best_path_of(self, consider_filetypes):
        for filetype in consider_filetypes:
            if filetype in self.match.tba_videos:
                return self.TBA_NET_VID_PATTERN % (self.match.event_key_name, self.match.key_name, filetype)
        return None
