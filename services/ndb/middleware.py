from google.cloud import ndb
from webapp2 import RequestContext

from services.ndb.gae_memcache_cache import ManagedMemcacheNdbCache

"""
Install a wsgi middleware object that creates an
ndb client context for each request

See https://cloud.google.com/appengine/docs/standard/python3/migrating-to-cloud-ndb#using_a_runtime_context_with_wsgi_frameworks
"""

client = ndb.Client()
global_cache = ManagedMemcacheNdbCache()


class NdbCacheRequestContext(RequestContext):

    def __init__(self, app, environ):
        self.ndb_client_context = client.context(global_cache=global_cache)
        super(NdbCacheRequestContext, self).__init__(app, environ)

    def __enter__(self):
        self.ndb_client_context.__enter__()
        return super(NdbCacheRequestContext, self).__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        self.ndb_client_context.__exit__(exc_type, exc_value, traceback)
        super(NdbCacheRequestContext, self).__exit__(exc_type, exc_value, traceback)


def install_middleware(app):
    app.request_context_class = NdbCacheRequestContext
