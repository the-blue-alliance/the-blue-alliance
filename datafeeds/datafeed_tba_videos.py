import logging
import re

from google.appengine.api import urlfetch
from google.appengine.ext import db

from BeautifulSoup import BeautifulSoup

from models import TBAVideo


class DatafeedTbaVideos(object):
    """
    Facilitates building TBAVideos store from TBA.
    """
    
    TBA_VIDS_DIR_URL_PATTERN = "http://thebluealliance.net/tbatv/vids/%s/"
    TBA_VIDS_VID_URL_PATTERN = "http://thebluealliance.net/tbatv/vids/%s/%s"
    SKIP_FILETYPES = ["jpg", "jpeg", "JPG", "JPEG"]
    
    def getEventVideosList(self, event):
        """
        Scrape all Videos for a given Event.
        """
        
        logging.info("Retreiving Videos for " + event.key().name())
        url = self.TBA_VIDS_DIR_URL_PATTERN % (event.key().name()[2:])
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            return self.parseEventVideos(result.content, event)
        else:
            logging.error('Unable to retreive url: ' + url)
            return None
    
    def parseEventVideos(self, html, event):
        """
        Parse the directory listing on TBA to extract relevant TBAVideo 
        information. Returns a list of TBAVideos
        """
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        matches = event.match_set
        match_dict = dict()
        for match in matches:
            match_dict.setdefault(match.key().name()[4:], match)
        
        tbavideos = list()
        
        for a in soup.findAll("a", href=True):
            
            logging.info(a)
            
            parts = a["href"].split(".")
            if len(parts) == 2:
                (key, filetype) = parts
            else:
                continue
                
            if filetype in self.SKIP_FILETYPES:
                continue
            
            if key in match_dict.keys():
                tbavideo = TBAVideo(
                    match = match_dict[key],
                    url = self.TBA_VIDS_VID_URL_PATTERN % (event.key().name()[2:], a["href"]),
                    filetype = filetype,
                )
                tbavideos.append(tbavideo)
            else:
                logging.info("Unexpected match: " + a["href"])
        
        return tbavideos

