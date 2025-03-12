import abc
import itertools
import json
import logging
import pickle
from collections import defaultdict
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    DefaultDict,
    Generic,
    Iterable,
    List,
    Optional,
    overload,
    Set,
    Type,
    TypeVar,
)

from google.appengine.ext import ndb

from backend.common.cache_clearing.get_affected_queries import TCacheKeyAndQuery
from backend.common.helpers.deferred import defer_safe
from backend.common.helpers.listify import delistify, listify
from backend.common.models.cached_model import CachedModel, TAffectedReferences
from backend.common.queries.database_query import CachedDatabaseQuery


TModel = TypeVar("TModel", bound=CachedModel)


@dataclass(frozen=True)
class TUpdatedModel(Generic[TModel]):
    model: TModel
    updated_attrs: Set[str]
    is_new: bool


class ManipulatorBase(abc.ABC, Generic[TModel]):
    _post_delete_hooks: List[Callable[[List[TModel]], None]] = None  # pyre-ignore[8]
    _post_update_hooks: List[  # pyre-ignore[8]
        Callable[[List[TUpdatedModel[TModel]]], None]
    ] = None

    def __init_subclass__(cls, *args, **kwargs):
        """
        This is a bit of python magic - we can't just initialize the variables to [] in their
        definitions above, because they simply get evaluated once at module import time. This
        has the effect that all manipulators end up -sharing- their callbacks! Not what we want!

        Instead, since we use python >= 3.6, we can use this __init_subclass__ hook, which
        makes specifying this sort of thing easier without needing to implement a full metaclass
        See: https://docs.python.org/3/reference/datamodel.html#object.__init_subclass__
        """
        super().__init_subclass__(*args, **kwargs)
        cls._post_delete_hooks = []
        cls._post_update_hooks = []

    @classmethod
    def register_post_delete_hook(
        cls, func: Callable[[List[TModel]], None]
    ) -> Callable[[List[TModel]], None]:
        cls._post_delete_hooks.append(func)
        return func

    @classmethod
    def register_post_update_hook(
        cls, func: Callable[[List[TUpdatedModel[TModel]]], None]
    ) -> Callable[[List[TUpdatedModel[TModel]]], None]:
        cls._post_update_hooks.append(func)
        return func

    @classmethod
    @abc.abstractmethod
    def updateMerge(
        cls,
        new_model: TModel,
        old_model: TModel,
        auto_union: bool,
        update_manual_attrs: bool,
    ) -> TModel:
        """
        Child classes should implement this method with specific merging logic
        """
        ...

    """
    createOrUpdate is the main interface to a manipulator - given a singular/list of models from a caller
    it will either create it in the ndb or do read-modify-write on the existing version
    """

    @overload
    @classmethod
    def createOrUpdate(
        cls,
        new_models: TModel,
        auto_union: bool = True,
        run_post_update_hook: bool = True,
        update_manual_attrs: bool = True,
    ) -> TModel: ...

    @overload
    @classmethod
    def createOrUpdate(
        cls,
        new_models: List[TModel],
        auto_union: bool = True,
        run_post_update_hook: bool = True,
        update_manual_attrs: bool = True,
    ) -> List[TModel]: ...

    @classmethod
    def createOrUpdate(
        cls,
        new_models,
        auto_union=True,
        run_post_update_hook=True,
        update_manual_attrs=True,
    ) -> Any:
        existing_or_new = listify(
            cls.findOrSpawn(new_models, auto_union, update_manual_attrs)
        )

        models_to_put = [model for model in existing_or_new if model._dirty]
        ndb.put_multi(models_to_put)
        cls._clearCache(existing_or_new)

        if run_post_update_hook:
            cls._run_post_update_hook(models_to_put)

        for model in existing_or_new:
            model._dirty = False

        return delistify(existing_or_new)

    """
    delete_keys / delete are the main interfaces to delete models + clear associated cache
    """

    @classmethod
    def delete_keys(cls, model_keys: Iterable[ndb.Key]) -> None:
        models = [model_key.get() for model_key in model_keys]
        cls.delete(models)

    @overload
    @classmethod
    def delete(self, models: TModel, run_post_delete_hook=True) -> None: ...

    @overload
    @classmethod
    def delete(self, models: List[TModel], run_post_delete_hook=True) -> None: ...

    @classmethod
    def delete(self, models, run_post_delete_hook=True) -> None:
        models = list(filter(None, listify(models)))
        keys = [model.key for model in models]
        ndb.delete_multi(keys)
        for model in models:
            model._dirty = True
            self._computeAndSaveAffectedReferences(model)
        if run_post_delete_hook:
            self._run_post_delete_hook(models)
        self._clearCache(models)

    @overload
    @classmethod
    def clearCache(cls, models: TModel) -> None: ...

    @overload
    @classmethod
    def clearCache(cls, models: List[TModel]) -> None: ...

    @classmethod
    def clearCache(cls, models) -> None:
        models = list(filter(None, listify(models)))
        for model in models:
            model._dirty = True
            cls._computeAndSaveAffectedReferences(model)
        cls._clearCache(models)

    """
    findOrSpawn will take either a singular model or a list of models and merge them
    with the (optionally present) existing versions
    """

    @overload
    @classmethod
    def findOrSpawn(
        cls,
        new_models: TModel,
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> TModel: ...

    @overload
    @classmethod
    def findOrSpawn(
        cls,
        new_models: List[TModel],
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> List[TModel]: ...

    @classmethod
    def findOrSpawn(cls, new_models, auto_union=True, update_manual_attrs=True) -> Any:
        new_models = listify(new_models)
        old_models = ndb.get_multi(
            [model.key for model in new_models], use_cache=False, use_memcache=False
        )
        updated_models = [
            cls.updateMergeBase(new_model, old_model, auto_union, update_manual_attrs)
            for (new_model, old_model) in zip(new_models, old_models)
        ]
        return delistify(updated_models)

    @classmethod
    def updateMergeBase(
        cls,
        new_model: TModel,
        old_model: Optional[TModel],
        auto_union: bool,
        update_manual_attrs: bool,
    ) -> TModel:
        """
        Given an "old" and a "new" model object, replace the fields in the
        "old" one that are present in the "new" one, but keep fields from
        the "old" one that are null or the empty list in the "new" one.
        """
        if old_model is None:
            new_model._dirty = True
            new_model._is_new = True
            cls._computeAndSaveAffectedReferences(new_model)
            return new_model

        cls._computeAndSaveAffectedReferences(old_model, new_model)
        return cls.updateMerge(new_model, old_model, auto_union, update_manual_attrs)

    @classmethod
    def mergeModels(
        self,
        new_models: List[TModel],
        old_models: List[TModel],
        auto_union: bool = True,
        update_manual_attrs: bool = True,
    ) -> List[TModel]:
        """
        Returns a list of models containing the union of new_models and old_models.
        If a model with the same key is in both input lists, the new_model is merged with the old_model.
        """
        old_models_by_key = {}
        untouched_old_keys = set()
        for model in old_models:
            model_key = model.key.id()
            old_models_by_key[model_key] = model
            untouched_old_keys.add(model_key)

        merged_models: List[TModel] = []
        for model in new_models:
            model_key = model.key.id()
            if model_key in old_models_by_key:
                merged_models.append(
                    self.updateMergeBase(
                        model,
                        old_models_by_key[model_key],
                        auto_union=auto_union,
                        update_manual_attrs=update_manual_attrs,
                    )
                )
                untouched_old_keys.remove(model_key)
            else:
                merged_models.append(model)

        for untouched_key in untouched_old_keys:
            merged_models.append(old_models_by_key[untouched_key])

        return merged_models

    @classmethod
    def _computeAndSaveAffectedReferences(
        cls, old_model: TModel, new_model: Optional[TModel] = None
    ) -> None:
        """
        This method is called whenever a model may potentially be created or updated.
        Stores the affected references in the original instance of the model.
        """

        for attr in old_model._affected_references.keys():
            for a in [old_model, new_model] if new_model is not None else [old_model]:
                val = listify(getattr(a, attr))
                old_model._affected_references[attr] = old_model._affected_references[
                    attr
                ].union(val)

    @classmethod
    def _run_post_delete_hook(cls, models: List[TModel]) -> None:
        """
        Asynchronously runs the manipulator's post delete hooks if available.
        """
        if not models:
            return

        for hook in cls._post_delete_hooks:
            defer_safe(
                hook,
                models,
                _queue="post-update-hooks",
                _target="py3-tasks-io",
                _url=f"/_ah/queue/deferred_{cls.__name__}_runPostDeleteHook",
            )

    @classmethod
    def _run_post_update_hook(cls, models: List[TModel]) -> None:
        """
        Asynchronously runs the manipulator's post update hooks if available.
        """
        if not models:
            return

        updated_models = [
            TUpdatedModel(
                model=model,
                updated_attrs=model._updated_attrs or set(),
                is_new=model._is_new,
            )
            for model in models
        ]

        # Split the models into batches to avoid exceeding the task payload limit.
        BATCH_BYTES_LIMIT = 600000  # Less than 1048487 bytes
        size_bytes = len(pickle.dumps(updated_models))
        bytes_per_model = size_bytes / len(updated_models)
        batch_size = int(BATCH_BYTES_LIMIT / bytes_per_model)
        logging.info(
            f"{cls.__name__}._run_post_update_hook() size of {len(updated_models)} updated models: {size_bytes}. Using batch size: {batch_size}"
        )
        for batch_models in itertools.batched(updated_models, batch_size):
            for hook in cls._post_update_hooks:
                defer_safe(
                    hook,
                    list(batch_models),
                    _queue="post-update-hooks",
                    _target="py3-tasks-io",
                    _url=f"/_ah/queue/deferred_{cls.__name__}_runPostUpdateHook",
                )

    """
    Helpers for subclasses
    """

    @staticmethod
    def _update_attrs(
        new_model: TModel,
        old_model: TModel,
        auto_union: bool,
        update_manual_attrs: bool,
    ) -> None:
        """
        Given an "old" and a "new" model, replace the fields in the
        "old" that are present in the "new", but keep fields from
        the "old" that are null in the "new".
        """
        updated_attrs: Set[str] = set()

        for attr in old_model._mutable_attrs:
            if not update_manual_attrs and attr in old_model.manual_attrs:
                continue

            if (
                getattr(new_model, attr, None) is not None
                or attr in old_model._allow_none_attrs
            ):
                if getattr(new_model, attr) != getattr(old_model, attr):
                    setattr(old_model, attr, getattr(new_model, attr))
                    updated_attrs.add(attr)
                    old_model._dirty = True
            if getattr(new_model, attr, None) == "None":
                if getattr(old_model, attr, None) is not None:
                    setattr(old_model, attr, None)
                    updated_attrs.add(attr)
                    old_model._dirty = True

        for attr in old_model._json_attrs:
            if not update_manual_attrs and attr in old_model.manual_attrs:
                continue

            if getattr(new_model, attr) is not None:
                if (getattr(old_model, attr) is None) or (
                    json.loads(getattr(new_model, attr))
                    != json.loads(getattr(old_model, attr))
                ):
                    setattr(old_model, attr, getattr(new_model, attr))
                    # changinging 'attr_json' doesn't clear lazy-loaded '_attr'
                    setattr(old_model, "_{}".format(attr.replace("_json", "")), None)
                    updated_attrs.add(attr)
                    old_model._dirty = True

        list_attrs = old_model._list_attrs.union({"manual_attrs"})
        if not auto_union:
            list_attrs = list_attrs.union(old_model._auto_union_attrs)
        for attr in list_attrs:
            if not update_manual_attrs and attr in old_model.manual_attrs:
                continue

            if len(getattr(new_model, attr)) > 0 or not auto_union:
                if getattr(new_model, attr) != getattr(old_model, attr):
                    setattr(old_model, attr, getattr(new_model, attr))
                    updated_attrs.add(attr)
                    old_model._dirty = True

        for attr in old_model._auto_union_attrs if auto_union else {}:
            if not update_manual_attrs and attr in old_model.manual_attrs:
                continue

            old_set = set(getattr(old_model, attr))
            new_set = set(getattr(new_model, attr))
            unioned = old_set.union(new_set)
            if unioned != old_set:
                setattr(old_model, attr, list(unioned))
                updated_attrs.add(attr)
                old_model._dirty = True

        old_model._updated_attrs = updated_attrs

    """
    cache clearing hook
    """

    @classmethod
    def _clearCache(cls, models: Iterable[TModel]) -> None:
        """
        Make deferred calls to clear caches
        Needs to save _affected_references and the dirty flag
        """
        all_affected_references: List[TAffectedReferences] = []
        for model in models:
            if model._dirty and model._affected_references:
                all_affected_references.append(model._affected_references)

        if all_affected_references:
            defer_safe(
                cls._clearCacheDeferred,
                all_affected_references,
                _queue="cache-clearing",
                # this does not exist in Cloud Tasks
                # _transactional=ndb.in_transaction(),
                _target="py3-tasks-io",
                _url=f"/_ah/queue/deferred_{cls.__name__}_clearCache",
            )

    @classmethod
    def _clearCacheDeferred(
        cls, all_affected_references: List[TAffectedReferences]
    ) -> None:
        to_clear: DefaultDict[Type[CachedDatabaseQuery], Set[str]] = defaultdict(set)
        for affected_references in all_affected_references:
            for cache_key, query in cls.getCacheKeysAndQueries(affected_references):
                to_clear[query].add(cache_key)

        for query, cache_keys in to_clear.items():
            query.delete_cache_multi(cache_keys)

    @classmethod
    @abc.abstractmethod
    def getCacheKeysAndQueries(
        cls, affected_refs: TAffectedReferences
    ) -> List[TCacheKeyAndQuery]:
        """
        Child classes should replace method with appropriate call to CacheClearer.
        """
        ...
