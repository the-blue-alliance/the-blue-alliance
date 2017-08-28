from controllers.apiv3.api_base_controller import ApiBaseController
from models.sitevar import Sitevar


class ApiAdminController(ApiBaseController):
    """
    Allow special admin-only endpoints for APIv3
    """
    REQUIRE_ADMIN_AUTH = True

    def get(self, *args, **kw):
        # We want these to be POST-only
        self.abort(405)


class ApiAdminSetBuildInfo(ApiAdminController):
    """
    A controller that allows us to set data about the currently deployed version
    """

    def _render(self):
        current_commit_sha = self.request.get('current_commit', '')
        commit_time = self.request.get('commit_time', '')
        build_time = self.request.get('build_time', '')
        deploy_time = self.request.get('deploy_time', '')
        travis_job = self.request.get('travis_job', '')

        web_info = {
            'current_commit': current_commit_sha,
            'commit_time': commit_time,
            'build_time': build_time,
            'deploy_time': deploy_time,
            'travis_job': travis_job,
        }

        status_sitevar = Sitevar.get_or_insert('apistatus', values_json='{}')
        contents = status_sitevar.contents
        contents['web'] = web_info
        status_sitevar.contents = contents
        status_sitevar.put()
