import os

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from helpers.memcache.memcache_webcast_flusher import MemcacheWebcastFlusher

# Main memcache view.
class AdminMemcacheMain(webapp.RequestHandler):
    def post(self):
        flushed = list()
        
        if self.request.get("all_keys") == "all_keys":
            memcache.flush_all()
            flushed.append("all memcache values")
            
        if self.request.get("webcast_keys") == "webcast_keys":
            flushed.append(MemcacheWebcastFlusher.flush())
        
        if self.request.get('memcache_key') is not "":
            memcache.delete(self.request.get("memcache_key"))
            flushed.append(self.request.get("memcache_key"))
        
        template_values = { 
            "flushed" : flushed,
            "memcache_stats": memcache.get_stats(),
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/memcache_index.html')
        self.response.out.write(template.render(path, template_values))

    def get(self):
        
        template_values = {
            "memcache_stats": memcache.get_stats(),
        }
        
        path = os.path.join(os.path.dirname(__file__), '../../templates/admin/memcache_index.html')
        self.response.out.write(template.render(path, template_values))
