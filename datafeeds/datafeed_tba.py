from datafeeds.datafeed_base import DatafeedBase

from datafeeds.tba_videos_parser import TbaVideosParser


class DatafeedTba(DatafeedBase):

    TBA_VIDS_DIR_URL_PATTERN = "http://videos.thebluealliance.net/%s/"

    def getVideos(self, event):
        url = self.TBA_VIDS_DIR_URL_PATTERN % (event.key_name)
        videos, _ = self.parse(url, TbaVideosParser)

        return videos
