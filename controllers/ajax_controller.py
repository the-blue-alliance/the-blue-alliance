import os
import json

from google.appengine.api import memcache
from google.appengine.ext.webapp import template

from base_controller import BaseHandler

from models.event import Event
from models.team import Team
import tba_config


class TypeaheadHandler(BaseHandler):
    def get(self):
        # Currently just returns a list of all teams and events
        # Needs to be optimized at some point.
        # Tried a trie but the datastructure was too big to
        # fit into memcache efficiently
        q = self.request.get_all('q')
        entries = self.typeahead_entries()

        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')        
        typeahead_list = json.dumps(entries)
        self.response.out.write(typeahead_list)
        
    def typeahead_entries(self):
        typeahead_key = "typeahead_entries"
        results = memcache.get(typeahead_key)
        
        if results is None:
            events = Event.all().order('-year').order('name')       
            teams = Team.all().order('team_number')

            results = []
            for event in events:
                results.append({'id': event.key().name(), 'name': '%s %s [%s]' % (event.year, event.name, event.event_short.upper())})
            for team in teams:
                results.append({'id': team.team_number, 'name': '%s | %s' % (team.team_number, team.nickname)})

            if tba_config.CONFIG["memcache"]: memcache.set(typeahead_key, results, 86400)
        return results
    
class WebcastHandler(BaseHandler):
    def get(self):
        # Returns the HTML necessary to generate the webcast embed for a given event
        event_key = self.request.get_all('event')[0]
        webcast_number = int(self.request.get_all('num')[0]) - 1
        webcast_key = "webcast_" + event_key
        output_json = memcache.get(webcast_key)
        
        if output_json is None:
            event = Event.get_by_key_name(event_key)
            if event:
                webcast = event.webcast[webcast_number]
                output = {}
                if webcast and 'type' in webcast and 'channel' in webcast:
                    webcast_type = webcast['type']
                    template_values = {'channel': webcast['channel']}
                    path = os.path.join(os.path.dirname(__file__), '../templates/webcast/' + webcast_type + '.html')
                    player = template.render(path, template_values)
                    output['player'] = player
                    
                output_json = json.dumps(output)
            if tba_config.CONFIG["memcache"]: memcache.set(webcast_key, output_json, 86400)
        
        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')        
        self.response.out.write(output_json)
