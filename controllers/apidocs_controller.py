import os

from google.appengine.ext.webapp import template

from consts.notification_type import NotificationType
from controllers.base_controller import CacheableHandler
from template_engine import jinja2_engine


class ApiDocumentationOverviewHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "api_docs_overview"

    def __init__(self, *args, **kw):
        super(ApiDocumentationOverviewHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/apidocs_overview.html")
        return template.render(path, self.template_values)


class ApiV2DocumentationHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "api_docs"

    def __init__(self, *args, **kw):
        super(ApiV2DocumentationHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/apidocs_v2.html")
        return template.render(path, self.template_values)


class ApiV3DocumentationHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "api_docs_v3"

    def __init__(self, *args, **kw):
        super(ApiV3DocumentationHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        self.template_values['title'] = 'APIv3'
        self.template_values['swagger_url'] = '/swagger/api_v3.json'
        path = os.path.join(os.path.dirname(__file__), "../templates/apidocs_swagger.html")
        return template.render(path, self.template_values)


class ApiTrustedDocumentationHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "api_docs_trusted_v1"

    def __init__(self, *args, **kw):
        super(ApiTrustedDocumentationHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        self.template_values['title'] = 'Trusted API'
        self.template_values['swagger_url'] = '/swagger/api_trusted_v1.json'
        path = os.path.join(os.path.dirname(__file__), "../templates/apidocs_swagger.html")
        return template.render(path, self.template_values)


class WebhookDocumentationHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "webhook_docs"

    def __init__(self, *args, **kw):
        super(WebhookDocumentationHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        self.template_values['enabled'] = NotificationType.enabled_notifications
        self.template_values['types'] = NotificationType.types
        path = os.path.join(os.path.dirname(__file__), "../templates/webhookdocs.html")
        return template.render(path, self.template_values)


class AddDataHandler(CacheableHandler):
    CACHE_VERSION = 1
    CACHE_KEY_FORMAT = "add_data_instructions"

    def __init__(self, *args, **kw):
        super(AddDataHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7

    def _render(self, *args, **kw):
        return jinja2_engine.render('add_data.html', self.template_values)
