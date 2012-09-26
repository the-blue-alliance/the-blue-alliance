from google.appengine.ext import db
from google.appengine.api import memcache

import tba_config

LEGAL_VALUES = {'landing': ['main', 'kickoff']}


class Vars(db.Model):
    """
    Vars are site wide variables that can be used to store
    site configurations and states.
    Keys can be anything.
    """

    value = db.StringProperty(required=True, indexed=False)

    @classmethod
    def get_or_insert_cached(cls, key_name, **kwds):
        memcache_key = "vars_%s" % key_name
        var = memcache.get(memcache_key)
        
        if var is None:
            var = Vars.get_or_insert(key_name, **kwds)
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, var, 86400) 
        return var

    @classmethod
    def get_all_cached(cls):
        memcache_key = "vars_all"
        vars_all = memcache.get(memcache_key)
        
        if vars_all is None:
            vars_all = Vars.all()
            if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, vars_all, 86400) 
        return vars_all
    
    def put_cached(self):
        self.put()
        memcache_key = "vars_%s" % self.key().name()
        memcache.delete(memcache_key)
