from google.appengine.ext import ndb
from helpers.cache_clearer import CacheClearer


class ManipulatorBase(object):
    """
    Provides a basic framework for manipulating db models.
    Ideally, all db read/writes would go through manipulators.
    """

    BATCH_SIZE = 500

    @classmethod
    def delete_keys(cls, model_keys):
        models = [model_key.get() for model_key in model_keys]
        cls.delete(models)

    @classmethod
    def delete(self, models):
        keys = [model.key for model in self.listify(models)]
        ndb.delete_multi(keys)
        for model in self.listify(models):
            if hasattr(model, '_affected_references'):
                self._computeAndSaveAffectedReferences(model)
                self.clearCache(model._affected_references)

    @classmethod
    def clearCache(cls, affected_refs):
        """
        Child classes should replace method with appropriate call to CacheClearer.
        """
        return

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
    def _computeAndSaveAffectedReferences(cls, old_model, new_model=None):
        """
        This method is called whenever a model may potentially be created or updated.
        Stores the affected references in the original instance of the model.
        """
        if hasattr(old_model, '_affected_references'):
            for attr in old_model._affected_references.keys():
                for a in [old_model, new_model] if new_model is not None else [old_model]:
                    val = cls.listify(getattr(a, attr))
                    old_model._affected_references[attr] = old_model._affected_references[attr].union(val)

    @classmethod
    def createOrUpdate(self, new_models, auto_union=True):
        """
        Given a model or list of models, either insert them into the database, or update
        existing models with the same key.
        """
        models = self.listify(self.findOrSpawn(self.listify(new_models), auto_union=auto_union))
        models_to_put = [model for model in models if getattr(model, "dirty", False)]
        ndb.put_multi(models_to_put)
        for model in models:
            if hasattr(model, '_affected_references') and getattr(model, 'dirty', False):
                self.clearCache(model._affected_references)
        return self.delistify(models)

    @classmethod
    def findOrSpawn(self, new_models, auto_union=True):
        """"
        Check if a model or models currently exists in the database based on
        key_name. Doesn't put models.
        If it does, update it and give it back. If it does not, give it back.
        """
        new_models = self.listify(new_models)
        old_models = ndb.get_multi([ndb.Key(type(model).__name__, model.key_name) for model in new_models])
        new_models = [self.updateMergeBase(new_model, old_model, auto_union=auto_union) for (new_model, old_model) in zip(new_models, old_models)]
        return self.delistify(new_models)

    @classmethod
    def updateMergeBase(self, new_model, old_model, auto_union=True):
        """
        Given an "old" and a "new" model object, replace the fields in the
        "old" one that are present in the "new" one, but keep fields from
        the "old" one that are null or the empty list in the "new" one.
        """
        if old_model is None:
            new_model.dirty = True
            self._computeAndSaveAffectedReferences(new_model)
            return new_model

        self._computeAndSaveAffectedReferences(old_model, new_model)
        return self.updateMerge(new_model, old_model, auto_union=auto_union)

    @classmethod
    def updateMerge(self, new_model, old_model, auto_union=True):
        """
        Child classes should replace with method with specific merging logic
        """
        raise NotImplementedError("No updateMerge method!")
