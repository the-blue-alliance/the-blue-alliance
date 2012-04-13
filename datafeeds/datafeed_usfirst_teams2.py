import logging

from google.appengine.api import urlfetch

from BeautifulSoup import BeautifulSoup

class DatafeedUsfirstTeams2(object):
    """
    Facilitates getting information about Teams from USFIRST.
    Reads from FMS data pages, which are mostly tab delimited files wrapped in some HTML.
    Note, this doesn't get team websites.
    """
    
    TEAMLIST_URL = "https://my.usfirst.org/frc/scoring/index.lasso?page=teamlist"
    
    def getAllCurrentSeasonTeams(self):
        result = urlfetch.fetch(self.TEAMLIST_URL)
        if result.status_code == 200:
            return self._parseHtml(result.content)
        else:
            logging.error('Unable to retreive url: %s' % url)
            return None
    
    
    def _parseHtml(self, html):
        """
        Parse the information table on USFIRSTs site to extract team information.
        Return a list of dictionaries of team data.
        """
        teams = list()
        soup = BeautifulSoup(html,
                convertEntities=BeautifulSoup.HTML_ENTITIES)
        
        for title in soup.findAll('title'):
            if title.string != "2012 FRC Team/Event List":
                return None
        
        team_rows = soup.findAll("pre")[0].string.split("\n")
        
        for line in team_rows[2:]: #first is blank, second is headers.
            data = line.split("\t")
            if len(data) > 1:
                try:
                    teams.append({
                        "team_number": int(data[1]),
                        "name": data[2],
                        "short_name": data[3],
                        "address": "%s, %s, %s" % (data[4], data[5], data[6]),
                        "nickname": data[7]
                    })
                except Exception, e:
                    logging.warning("Failed to parse team row: %s" % data)
        
        return teams
