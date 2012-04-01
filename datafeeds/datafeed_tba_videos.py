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
    
    TBA_VIDS_DIR_URL_PATTERN = "http://videos.thebluealliance.com/%s/"
    
    def getEventVideosList(self, event):
        """
        Scrape all Videos for a given Event.
        """
        
        logging.info("Retreiving Videos for " + event.get_key_name())
        url = self.TBA_VIDS_DIR_URL_PATTERN % (event.get_key_name())
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
        match_filetypes = dict()
        
        try:
            for match in matches:
                # Note: get_key_name() doesn't always return the key().name()
                # because of things like malformed Championship Field names. -gregmarra
                match_dict.setdefault(match.get_key_name(), match)
        except Exception, e:
            logging.error("Malformed match in Event %s" % event.key().name())
        
        for a in soup.findAll("a", href=True):
            parts = a["href"].split(".")
            if len(parts) == 2:
                (key, filetype) = parts
            else:
                logging.info("Malformed video filename: " + a["href"])
                continue
                
            if key in match_dict:
                match_filetypes.setdefault(key, list())
                match_filetypes[key].append(filetype)
            else:
                logging.info("Unexpected match: " + key)
        
        tbavideos = list()
        
        return match_filetypes
        
        for match_key in match_filetypes.keys():
            tbavideo = TBAVideo(
                match = match_dict[match_key],
                filetypes = match_filetypes[match_key],
            )
            tbavideos.append(tbavideo)            
        
        return tbavideos

