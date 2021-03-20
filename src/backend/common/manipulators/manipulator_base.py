import abc
import json
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

from google.cloud import ndb

from backend.common.cache_clearing.get_affected_queries import TCacheKeyAndQuery
from backend.common.deferred import defer
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
        cls, new_model: TModel, old_model: TModel, auto_union: bool
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
    ) -> TModel:
        ...

    @overload
    @classmethod
    def createOrUpdate(
        cls,
        new_models: List[TModel],
        auto_union: bool = True,
        run_post_update_hook: bool = True,
    ) -> List[TModel]:
        ...

    @classmethod
    def createOrUpdate(
        cls, new_models, auto_union=True, run_post_update_hook=True
    ) -> Any:
        existing_or_new = listify(cls.findOrSpawn(new_models, auto_union))

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
    def delete(self, models: TModel, run_post_delete_hook=True) -> None:
        ...

    @overload
    @classmethod
    def delete(self, models: List[TModel], run_post_delete_hook=True) -> None:
        ...

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

    """
    findOrSpawn will take either a singular model or a list of models and merge them
    with the (optionally present) existing versions
    """

    @overload
    @classmethod
    def findOrSpawn(cls, new_models: TModel, auto_union: bool = True) -> TModel:
        ...

    @overload
    @classmethod
    def findOrSpawn(
        cls, new_models: List[TModel], auto_union: bool = True
    ) -> List[TModel]:
        ...

    @classmethod
    def findOrSpawn(cls, new_models, auto_union=True) -> Any:
        new_models = listify(new_models)
        old_models = ndb.get_multi(
            [model.key for model in new_models], use_cache=False, use_global_cache=False
        )
        updated_models = [
            cls.updateMergeBase(new_model, old_model, auto_union)
            for (new_model, old_model) in zip(new_models, old_models)
        ]
        return delistify(updated_models)

    @classmethod
    def updateMergeBase(
        cls, new_model: TModel, old_model: Optional[TModel], auto_union
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
        return cls.updateMerge(new_model, old_model, auto_union)

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
            defer(
                hook,
                models,
                _queue="post-update-hooks",
                _target="tasks-io",
                _url="/_ah/queue/deferred_manipulator_runPostDeleteHook",
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
        for hook in cls._post_update_hooks:
            defer(
                hook,
                updated_models,
                _queue="post-update-hooks",
                _target="tasks-io",
                _url="/_ah/queue/deferred_manipulator_runPostUpdateHook",
            )

    """
    Helpers for subclasses
    """

    @staticmethod
    def _update_attrs(new_model: TModel, old_model: TModel, auto_union: bool) -> None:
        """
        Given an "old" and a "new" model, replace the fields in the
        "old" that are present in the "new", but keep fields from
        the "old" that are null in the "new".
        """
        updated_attrs: Set[str] = set()

        for attr in old_model._mutable_attrs:
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

        list_attrs = old_model._list_attrs
        if not auto_union:
            list_attrs = list_attrs.union(old_model._auto_union_attrs)
        for attr in list_attrs:
            if len(getattr(new_model, attr)) > 0 or not auto_union:
                if getattr(new_model, attr) != getattr(old_model, attr):
                    setattr(old_model, attr, getattr(new_model, attr))
                    updated_attrs.add(attr)
                    old_model._dirty = True

        for attr in old_model._auto_union_attrs if auto_union else {}:
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
            defer(
                cls._clearCacheDeferred,
                all_affected_references,
                _queue="cache-clearing",
                # this does not exist in Cloud Tasks
                # _transactional=ndb.in_transaction(),
                _target="tasks-io",
                _url="/_ah/queue/deferred_manipulator_clearCache",
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
