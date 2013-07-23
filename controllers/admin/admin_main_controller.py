import os
import json
import re

from google.appengine.ext.webapp import template

from controllers.base_controller import LoggedInHandler

class AdminMain(LoggedInHandler):
    def get(self):
        self._require_admin()
        
        # version info
        fname = os.path.join(os.path.dirname(__file__), '../../version_info.json')
        with open(fname, 'r') as f:
            data = json.loads(f.read())
        self.template_values['git_branch_name'] = data['git_branch_name']
        commit_hash, commit_author, commit_date, commit_msg, _ = re.split("[\r\n]+", data['git_last_commit'])
        self.template_values['commit_hash'] = commit_hash
        self.template_values['commit_author'] = commit_author
        self.template_values['commit_date'] = commit_date
        self.template_values['commit_msg'] = commit_msg
        self.template_values['build_time'] = data['build_time']
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/index.html')
        self.response.out.write(template.render(path, self.template_values))

class AdminDebugHandler(LoggedInHandler):
    def get(self):
        self._require_admin()
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/debug.html')
        self.response.out.write(template.render(path, self.template_values))

class AdminTasksHandler(LoggedInHandler):
    def get(self):
        self._require_admin()
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/tasks.html')
        self.response.out.write(template.render(path, self.template_values))