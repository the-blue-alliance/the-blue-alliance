import json
import logging
import os

from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from models.event import Event
from models.award import Award
from models.team import Team
from helpers.award_manipulator import AwardManipulator


class AdminAwardDashboard(webapp.RequestHandler):
    """
    Show stats about Awards
    """
    def get(self):
        award_count = Award.query().count()
        
        template_values = {
            "award_count": award_count
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/award_dashboard.html')
        self.response.out.write(template.render(path, template_values))


class AdminAwardAdd(webapp.RequestHandler):
    """
    Add Award from JSON.
    """
    def post(self):
        event_key = self.request.get('event_key')
        awards_json = self.request.get('awards_json')
        awards = json.loads(awards_json)
        
        event = Event.get_by_id(event_key)
        
        def _getTeamKey(award):
            team = Team.get_by_id('frc' + str(award.get('team_number', None)))
            if team is not None:
                return team.key
            else:
                return None
       
        awards = [Award(
            id = Award.renderKeyName(event.key_name, award.get('name')),
            name = award.get('name', None),
            team = _getTeamKey(award),
            awardee = award.get('awardee', None),
            year = event.year,
            official_name = award.get('official_name', None),
            event = event.key)
            for award in awards]
        
        AwardManipulator.createOrUpdate(awards)
        self.redirect('/admin/event/{}'.format(event_key))


class AdminAwardEdit(webapp.RequestHandler):
    """
    Edit an Award.
    """
    def get(self, award_key):
        award = Award.get_by_id(award_key)
                
        template_values = {
            "award": award
        }

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/award_edit.html')
        self.response.out.write(template.render(path, template_values))
    
    def post(self, award_key):
        event_key_name = self.request.get('event_key_name')
        award = Award(
            id = award_key,
            name = self.request.get('award_name'),
            event = Event.get_by_id(event_key_name).key,
            official_name = self.request.get('official_name'),
            team = Team.get_by_id(self.request.get('team_key')).key,
            awardee = self.request.get('awardee'),
        )
        award = AwardManipulator.createOrUpdate(award)
        self.redirect("/admin/event/" + event_key_name)
