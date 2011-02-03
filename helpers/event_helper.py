import logging

from google.appengine.ext import db

from models import Event

class EventUpdater(object):
    """
    Helper class to handle Event objects when we are not sure whether they
    already exist or not.
    """
    
    @classmethod
    def createOrUpdate(self, new_event):
        """
        Take an Event object, and either update the Event it is a newer
        version of, or create the Event if it is totally new.
        """
        event = self.findOrSpawn(new_event)
        event.put()
        return event
    
    @classmethod
    def findOrSpawn(self, new_event):
        """"
        Check if an event currently exists in the database based on key_name.
        Doesn't put objects.
        If it does, update it and give it back.
        If it does not, give it back.
        """
        query = Event.all()
        
        # First, look for a key_name collision.
        event = Event.get_by_key_name(new_event.get_key_name())
        if event is not None:
            event = self.updateMerge(new_event, event)
            return event
        
        # Don't see it, give it back.
        return new_event
    
    @classmethod
    def updateMerge(self, new_event, old_event):
        """
        Given an "old" and a "new" Event object, replace the fields in the
        "old" event that are present in the "new" event, but keep fields from
        the "old" event that are null in the "new" event.
        """
        #FIXME: There must be a way to do this elegantly. -greg 5/12/2010
        
        if new_event.name is not None:
            old_event.name = new_event.name
        if new_event.event_type is not None:
            old_event.event_type = new_event.event_type
        if new_event.short_name is not None:
            old_event.short_name = new_event.short_name
        if new_event.event_short is not None:
            old_event.event_short = new_event.event_short
        if new_event.year is not None:
            old_event.year = new_event.year
        if new_event.start_date is not None:
            old_event.start_date = new_event.start_date
        if new_event.end_date is not None:
            old_event.end_date = new_event.end_date
        if new_event.venue is not None:
            old_event.venue = new_event.venue
        if new_event.venue_address is not None:
            old_event.venue_address = new_event.venue_address
        if new_event.website is not None:
            old_event.website = new_event.website
        if new_event.location is not None:
            old_event.location = new_event.location
        if new_event.official is not None:
            old_event.official = new_event.official
        if new_event.first_eid is not None:
            old_event.first_eid = new_event.first_eid
        if new_event.facebook_eid is not None:
            old_event.facebook_eid = new_event.facebook_eid
        
        old_event.put()
        return old_event