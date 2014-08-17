from collections import defaultdict
from google.appengine.ext import deferred
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
        models = self.listify(models)
        keys = [model.key for model in models]
        ndb.delete_multi(keys)
        for model in models:
            model.dirty = True
            self._computeAndSaveAffectedReferences(model)
        self._clearCache(models)

    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        """
        Child classes should replace method with appropriate call to CacheClearer.
        """
        return []

    @classmethod
    def _clearCache(cls, models):
        to_clear = defaultdict(set)
        for model in models:
            if hasattr(model, '_affected_references') and getattr(model, 'dirty', False):
                for cache_key, controller in cls.getCacheKeysAndControllers(model._affected_references):
                    to_clear[controller].add(cache_key)
            if hasattr(model, 'dirty'):
                model.dirty = False

        for controller, cache_keys in to_clear.items():
            controller.delete_cache_multi(cache_keys)

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
    def createOrUpdate(self, new_models, auto_union=True, run_post_update_hook=True):
        """
        Given a model or list of models, either insert them into the database, or update
        existing models with the same key.
        Once inserted or updated, the model can be marked not dirty.
        """
        models = self.listify(self.findOrSpawn(self.listify(new_models), auto_union=auto_union))
        models_to_put = [model for model in models if getattr(model, "dirty", False)]
        ndb.put_multi(models_to_put)
        self._clearCache(models)
        if run_post_update_hook:
            self.runPostUpdateHook(models_to_put)
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

    @classmethod
    def runPostUpdateHook(cls, models):
        """
        Asynchronously runs the manipulator's post update hook if available.
        """
        post_update_hook = getattr(cls, "postUpdateHook", None)
        if callable(post_update_hook):
            for model in models:
                deferred.defer(post_update_hook, model, _queue="post-update-hooks")
