import logging

from google.appengine.ext import db

from models.award import Award

class AwardHelper(object):
    """
    Helper to prepare awards for being used in a template
    """
    @classmethod
    def organizeAwards(self, award_list):
        awards = dict([(award.name, award) for award in award_list])
        awards['list'] = award_list
        return awards
    

class AwardUpdater(object):
    """
    Helper class to handle Award objects when we are not sure whether they
    already exist or not.
    """
    
    def __init__(self):
        self.cached_awards = dict() # a dictionary to cache DB reads
    
    def bulkRead(self, award_list):
        """
        Take a list of awards, bulk read them to reduce DB reads.
        """
        keys = [award.key().name() for award in award_list]
        for award in Award.get_by_key_name(keys):
            if award is not None:
                self.cached_awards.setdefault(awards.key().name(), awards)
    
    @classmethod
    def createOrUpdate(self, new_award):
        """
        Get a handle on an Award, then write it down.
        """
        new_award = self.findOrSpawn(new_award)
        new_award.put()
        return new_award
    
    # There must be a more elegant way to do this -gregmarra 4 Mar 2012
    def findOrSpawnWithCache(self, new_award):
        """
        A version of findOrSpawn that can use the cache.
        """
        award = self.cached_awards.get(new_award.get_key_name(), None)
        if award is not None:
            new_award = self.updateMerge(new_award, award)
        else:
            new_award = self.findOrSpawn(new_award)
        
        return new_award
    
    @classmethod
    def findOrSpawn(self, new_award):
        """
        Check whether an award already exists. 
        If it does, update the data, and send it back.
        If it doesn't, send it back.
        """
        award = Award.get_by_key_name(new_award.get_key_name())
        if award is not None:
            new_award = self.updateMerge(new_award, match)
        
        return new_award
    
    @classmethod
    def updateMerge(self, new_award, old_award):
        """
        Merges the information in a new award object with the existing object
        representing that award.
        """
        #FIXME: There must be a way to do this elegantly. -greg 5/12/2010
        
        if new_award.official_name is not None:
            old_award.official_name = new_award.official_name
        if new_award.winner is not None:
            old_award.winner = new_award.winner
        if new_award.awardee is not None:
            old_award.awardee = new_award.awardee
        
        return old_award