import logging

from google.appengine.ext import ndb

class ManipulatorBase(object):
    """
    Provides a basic framework for manipulating db models.
    Ideally, all db read/writes would go through manipulators.
    """

    BATCH_SIZE = 500

    @classmethod
    def listify(self, thing):
        if not isinstance(thing, list):
            return [thing]
        else:
            return thing

    @classmethod
    def delistify(self, things):
        if len(things) == 0:
            return None
        if len(things) == 1:
            return things.pop()
        else:
            return things

    @classmethod
    def createOrUpdate(self, new_models):
        """
        Given a model or list of models, either insert them into the database, or update
        existing models with the same key.
        """
        new_models = self.listify(new_models)

        return_models = []
        async_puts = []

        while len(new_models) > 0:
            model_batch = new_models[-self.BATCH_SIZE:] # the last BATCH_SIZE items (or all of them)
            new_models = new_models[:-self.BATCH_SIZE] # everything but the last BATCH_SIZE items (or nothing)

            # Get the full list of db-merged models
            model_batch = self.listify(self.findOrSpawn(model_batch))
            return_models.extend(model_batch)

            # Write back the models that had updates
            models_to_put = [model for model in model_batch if getattr(model, "dirty", False)]
            async_puts.extend(ndb.put_multi_async(models_to_put))

        # Block on the entire batch to ensure consistency
        ndb.Future.wait_all(async_puts)
        return self.delistify(return_models)
    
    @classmethod
    def findOrSpawn(self, new_models):
        """"
        Check if a model or models currently exists in the database based on
        key_name. Doesn't put models.
        If it does, update it and give it back. If it does not, give it back.
        """
        new_models = self.listify(new_models)

        old_models = ndb.get_multi([ndb.Key(type(model).__name__, model.key_name) for model in new_models])
        new_models = [self.updateMergeBase(new_model, old_model) for (new_model, old_model) in zip(new_models, old_models)]

        return self.delistify(new_models)
    
    @classmethod
    def updateMergeBase(self, new_model, old_model):
        """
        Given an "old" and a "new" model object, replace the fields in the
        "old" one that are present in the "new" one, but keep fields from
        the "old" one that are null or the empty list in the "new" one.
        """
        if old_model is None:
            new_model.dirty = True
            return new_model

        return self.updateMerge(new_model, old_model)

    @classmethod
    def updateMerge(self, new_model, old_model):
        """
        Child classes should replace with method with specific merging logic
        """
        raise NotImplementedError("No updateMerge method!")
