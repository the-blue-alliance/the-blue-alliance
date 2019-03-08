from collections import defaultdict
from google.appengine.ext import deferred
from google.appengine.ext import ndb
from helpers.cache_clearer import CacheClearer
import tba_config


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
    def delete(self, models, run_post_delete_hook=True):
        models = filter(None, self.listify(models))
        keys = [model.key for model in models]
        ndb.delete_multi(keys)
        for model in models:
            model.dirty = True
            self._computeAndSaveAffectedReferences(model)
        if run_post_delete_hook:
            self.runPostDeleteHook(models)
        self._clearCache(models)

    @classmethod
    def getCacheKeysAndControllers(cls, affected_refs):
        """
        Child classes should replace method with appropriate call to CacheClearer.
        """
        return []

    @classmethod
    def _clearCache(cls, models):
        """
        Makes a deferred call to clear cache.
        Needs to save _affected_references and dirty flag
        """
        if not tba_config.CONFIG['database_query_cache'] and not tba_config.CONFIG['response_cache']:
            return

        all_affected_references = []
        for model in models:
            if getattr(model, 'dirty', False) and hasattr(model, '_affected_references'):
                all_affected_references.append(model._affected_references)

        if all_affected_references != []:
            deferred.defer(
                cls._clearCacheDeferred,
                all_affected_references,
                _queue='cache-clearing',
                _transactional=ndb.in_transaction(),
                _target='default',
                _url='/_ah/queue/deferred_manipulator_clearCache'
            )

    @classmethod
    def _clearCacheDeferred(cls, all_affected_references):
        to_clear = defaultdict(set)
        for affected_references in all_affected_references:
            for cache_key, controller in cls.getCacheKeysAndControllers(affected_references):
                to_clear[controller].add(cache_key)

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
        for model in models:
            if model:  # Model can be None
                model.dirty = False
        return self.delistify(models)

    @classmethod
    def findOrSpawn(self, new_models, auto_union=True):
        """"
        Check if a model or models currently exists in the database based on
        key_name. Doesn't put models.
        If it does, update it and give it back. If it does not, give it back.
        """
        new_models = self.listify(new_models)
        old_models = ndb.get_multi([model.key for model in new_models], use_cache=False)
        new_models = [self.updateMergeBase(new_model, old_model, auto_union=auto_union) for (new_model, old_model) in zip(new_models, old_models)]
        return self.delistify(new_models)

    @classmethod
    def mergeModels(self, new_models, old_models, auto_union=True):
        """
        Returns a list of models containing the union of new_models and old_models.
        If a model with the same key is in both input lists, the new_model is merged with the old_model.
        """
        if new_models is None:
            new_models = []
        if old_models is None:
            old_models = []

        new_models = self.listify(new_models)
        old_models = self.listify(old_models)

        old_models_by_key = {}
        untouched_old_keys = set()
        for model in old_models:
            model_key = model.key.id()
            old_models_by_key[model_key] = model
            untouched_old_keys.add(model_key)

        merged_models = []
        for model in new_models:
            model_key = model.key.id()
            if model_key in old_models_by_key:
                merged_models.append(self.updateMergeBase(model, old_models_by_key[model_key], auto_union=auto_union))
                untouched_old_keys.remove(model_key)
            else:
                merged_models.append(model)

        for untouched_key in untouched_old_keys:
            merged_models.append(old_models_by_key[untouched_key])

        return self.delistify(merged_models)

    @classmethod
    def updateMergeBase(self, new_model, old_model, auto_union=True):
        """
        Given an "old" and a "new" model object, replace the fields in the
        "old" one that are present in the "new" one, but keep fields from
        the "old" one that are null or the empty list in the "new" one.
        """
        if old_model is None:
            new_model.dirty = True
            new_model._is_new = True  # used for post update/delete hooks
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
    def runPostDeleteHook(cls, models):
        """
        Asynchronously runs the manipulator's post delete hook if available.
        """
        if models:
            post_delete_hook = getattr(cls, "postDeleteHook", None)
            if callable(post_delete_hook):
                deferred.defer(post_delete_hook, models, _queue="post-update-hooks", _url='/_ah/queue/deferred_manipulator_runPostDeleteHook')

    @classmethod
    def runPostUpdateHook(cls, models):
        """
        Asynchronously runs the manipulator's post update hook if available.
        """
        if models:
            post_update_hook = getattr(cls, "postUpdateHook", None)
            if callable(post_update_hook):
                updated_attrs = [model._updated_attrs if hasattr(model, '_updated_attrs') else [] for model in models]
                is_new = [model._is_new if hasattr(model, '_is_new') else False for model in models]
                deferred.defer(post_update_hook, models, updated_attrs, is_new, _queue="post-update-hooks", _url='/_ah/queue/deferred_manipulator_runPostUpdateHook')
