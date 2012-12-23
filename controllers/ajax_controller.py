import os
import json

from google.appengine.api import memcache
from google.appengine.ext.webapp import template

from base_controller import BaseHandler

from models.event import Event
from models.team import Team
from models.sitevar import Sitevar
import tba_config


class TypeaheadHandler(BaseHandler):
    def get(self):
        # Currently just returns a list of all teams and events
        # Needs to be optimized at some point.
        # Tried a trie but the datastructure was too big to
        # fit into memcache efficiently
        
        # Only allow AJAX requests
        if (('x-requested-with' not in self.request.headers) or (self.request.headers['x-requested-with' ]!= 'XMLHttpRequest')):
            return self.redirect("/error/404")
        
        q = self.request.get_all('q')
        entries = self.typeahead_entries()

        self.response.headers['Cache-Control'] = "public, max-age=%d" % (6*60*60)
        self.response.headers['Pragma'] = 'Public'
        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')        
        typeahead_list = json.dumps(entries)
        self.response.out.write(typeahead_list)
        
    def typeahead_entries(self):
        typeahead_key = "typeahead_entries"
        results = memcache.get(typeahead_key)
        
        if results is None:
            events = Event.query().order(-Event.year).order(Event.name)       
            teams = Team.query().order(Team.team_number)

            results = []
            for event in events:
                results.append({'id': event.key_name, 'name': '%s %s [%s]' % (event.year, event.name, event.event_short.upper())})
            for team in teams:
                if not team.nickname:
                    nickname = "Team %s" % team.team_number
                else:
                    nickname = team.nickname
                results.append({'id': team.team_number, 'name': '%s | %s' % (team.team_number, nickname)})

            if tba_config.CONFIG["memcache"]: memcache.set(typeahead_key, results, 86400)
        return results
    
class WebcastHandler(BaseHandler):
    def get(self):
        # Only allow AJAX requests
        if (('x-requested-with' not in self.request.headers) or (self.request.headers['x-requested-with' ]!= 'XMLHttpRequest')):
            return self.redirect("/error/404")
      
        # Returns the HTML necessary to generate the webcast embed for a given event
        event_key = self.request.get_all('event')[0]
        webcast_number = int(self.request.get_all('num')[0]) - 1
        webcast_key = "webcast_" + event_key
        output_json = memcache.get(webcast_key)
        
        if output_json is None:
            event = Event.get_by_id(event_key)
            output = {}
            if event and event.webcast:
                webcast = event.webcast[webcast_number]
                if 'type' in webcast and 'channel' in webcast:
                    output['player'] = self._renderPlayer(webcast)
            else:
                special_webcasts_future = Sitevar.get_by_id_async('gameday.special_webcasts')
                special_webcasts = special_webcasts_future.get_result()
                if special_webcasts:
                    special_webcasts = special_webcasts.contents
                else:
                    special_webcasts = {}
                if event_key in special_webcasts:
                    webcast = special_webcasts[event_key]
                    if 'type' in webcast and 'channel' in webcast:
                        output['player'] = self._renderPlayer(webcast)                   
                    
            output_json = json.dumps(output)
            if tba_config.CONFIG["memcache"]: memcache.set(webcast_key, output_json, 86400)
        
        self.response.headers['Cache-Control'] = "public, max-age=%d" % (5*60)
        self.response.headers['Pragma'] = 'Public'
        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')        
        self.response.out.write(output_json)
        
    def _renderPlayer(self, webcast):
        webcast_type = webcast['type']
        template_values = {'channel': webcast['channel']}
        path = os.path.join(os.path.dirname(__file__), '../templates/webcast/' + webcast_type + '.html')
        return template.render(path, template_values)
