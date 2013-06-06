from google.appengine.ext import ndb
from models.datastore_cache_entry import DatastoreCacheEntry

class DatastoreCache(object):
  """
  Contains useful helper methods for interacting with the DatastoreCache
  API designed to be much like that of memcache
  """
  
  @classmethod
  def set(self, key, value):
    entry = DatastoreCacheEntry(id=key, value=value)
    entry.put()

  @classmethod
  def get(self, key):
    entry_future = DatastoreCacheEntry.get_by_id_async(key)
    entry = entry_future.get_result()
    if entry is None:
      return None
    return entry.value
  
  @classmethod
  def delete(self, key):
    entry_key = ndb.Key(DatastoreCacheEntry, key)
    entry_key.delete()
    
  @classmethod
  def cleanup(self, datetime):
    """
    Delete all entries that were last updated before a certain datetime
    """
    pass  # TODO: implement
