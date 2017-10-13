import json
import logging
import os

from google.appengine.ext import ndb
from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler
from datafeeds.csv_awards_parser import CSVAwardsParser
from helpers.award_manipulator import AwardManipulator
from models.award import Award
from models.event import Event
from models.team import Team


class AdminAwardDashboard(LoggedInHandler):
    """
    Show stats about Awards
    """
    def get(self):
        self._require_admin()
        award_count = Award.query().count()

        self.template_values.update({
            "award_count": award_count
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/award_dashboard.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminAwardDelete(LoggedInHandler):
    """
    Delete an award by ID
    """

    def post(self):
        award_key = self.request.get('award_key')
        if not award_key:
            self.abort(400)
        award = Award.get_by_id(award_key)
        if not award:
            self.abort(404)

        AwardManipulator.delete(award)
        self.redirect('/admin/awards')


class AdminAwardAddWithEvent(LoggedInHandler):
    """
    Add awards from csv, all with a single event
    """
    def post(self, event_key):
        self._require_admin()
        event = Event.get_by_id(event_key)
        if not event:
            self.abort(404)
        awards_csv = self.request.get('awards_csv')
        csv_lines = awards_csv.split('\n')
        pre = map(lambda award: "{},{},{}".format(event.year, event.event_short, award), csv_lines)
        updated_lines = '\n'.join(pre)
        new_awards = AdminAwardAdd.add_awards_from_csv(updated_lines)
        self.template_values = {
            'awards': new_awards,
        }
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/awards_add.html')
        self.response.out.write(template.render(path, self.template_values))


class AdminAwardAdd(LoggedInHandler):
    """
    Add Award from CSV.
    """
    def post(self):
        self._require_admin()
        awards_csv = self.request.get('awards_csv')
        new_awards = AdminAwardAdd.add_awards_from_csv(awards_csv)

        self.template_values = {
            'awards': new_awards,
        }
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/awards_add.html')
        self.response.out.write(template.render(path, self.template_values))

    @classmethod
    def add_awards_from_csv(cls, awards_csv):
        events = {}  # for reducing datastore fetches of events and teams
        awards = []
        for award in CSVAwardsParser.parse(awards_csv):
            event_key_name = '{}{}'.format(award['year'], award['event_short'])
            if event_key_name in events:
                event = events[event_key_name]
            else:
                event = Event.get_by_id(event_key_name)
                if event is None:
                    logging.warning("Event: {} doesn't exist!".format(event_key_name))
                    continue
                events[event_key_name] = event

            awards.append(Award(
                id=Award.render_key_name(event.key_name, award['award_type_enum']),
                name_str=award['name_str'],
                award_type_enum=award['award_type_enum'],
                year=event.year,
                event=event.key,
                event_type_enum=event.event_type_enum,
                team_list=[ndb.Key(Team, 'frc{}'.format(team_number)) for team_number in award['team_number_list']],
                recipient_json_list=award['recipient_json_list']
            ))

        new_awards = AwardManipulator.createOrUpdate(awards)
        if type(new_awards) != list:
            new_awards = [new_awards]
        return new_awards


class AdminAwardEdit(LoggedInHandler):
    """
    Edit an Award.
    """
    def get(self, award_key):
        self._require_admin()
        award = Award.get_by_id(award_key)

        self.template_values.update({
            "award": award
        })

        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/award_edit.html')
        self.response.out.write(template.render(path, self.template_values))

    def post(self, award_key):
        self._require_admin()

        event_key_name = self.request.get('event_key_name')

        recipient_json_list = []
        team_list = []
        for recipient in json.loads(self.request.get('recipient_list_json')):
            recipient_json_list.append(json.dumps(recipient))
            if recipient['team_number'] is not None:
                team_list.append(ndb.Key(Team, 'frc{}'.format(recipient['team_number'])))

        award = Award(
            id=award_key,
            name_str=self.request.get('name_str'),
            award_type_enum=int(self.request.get('award_type_enum')),
            event=ndb.Key(Event, event_key_name),
            event_type_enum=int(self.request.get('event_type_enum')),
            team_list=team_list,
            recipient_json_list=recipient_json_list,
        )
        award = AwardManipulator.createOrUpdate(award, auto_union=False)
        self.redirect("/admin/event/" + event_key_name)
