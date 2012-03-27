import os

from google.appengine.dist import use_library
use_library('django', '1.2')

ROOTDIR = os.path.abspath(os.path.dirname(__file__)) 
TEMPLATE_DIRS = (
    ROOTDIR + '/templates',
)

def webapp_add_wsgi_middleware(app):
   from google.appengine.ext.appstats import recording
   app = recording.appstats_wsgi_middleware(app)
   return app
