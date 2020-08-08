import abc
from typing import Any, Generic, List, Optional, overload, Set, TypeVar

from google.cloud import ndb

from backend.common.helpers.listify import delistify, listify
from backend.common.models.cached_model import CachedModel


TModel = TypeVar("TModel", bound=CachedModel)


class ManipulatorBase(abc.ABC, Generic[TModel]):
    @classmethod
    @abc.abstractmethod
    def updateMerge(
        cls, new_model: TModel, old_model: TModel, auto_union: bool = True
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
    def createOrUpdate(cls, new_models: TModel, auto_union: bool = True) -> TModel:
        ...

    @overload
    @classmethod
    def createOrUpdate(
        cls, new_models: List[TModel], auto_union: bool = True
    ) -> List[TModel]:
        ...

    @classmethod
    def createOrUpdate(cls, new_models, auto_union=True) -> Any:
        existing_or_new = listify(cls.findOrSpawn(new_models, auto_union))

        models_to_put = [model for model in existing_or_new if model._dirty]
        ndb.put_multi(models_to_put)
        cls._clearCache(existing_or_new)

        for model in existing_or_new:
            model._dirty = False

        return delistify(existing_or_new)

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
        old_models = ndb.get_multi([model.key for model in new_models], use_cache=False)
        if old_models:
            print([m.__class__ for m in old_models])
            print([dir(m) for m in old_models])

        updated_models = [
            cls.updateMergeBase(new_model, old_model, auto_union)
            for (new_model, old_model) in zip(new_models, old_models)
        ]
        return delistify(updated_models)

    @classmethod
    def updateMergeBase(
        cls, new_model: TModel, old_model: Optional[TModel], auto_union=True
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

    """
    Helpers for subclasses
    """

    @staticmethod
    def _update_attrs(new_model: TModel, old_model: TModel, attrs: Set[str]) -> None:
        for attr in attrs:
            if getattr(new_model, attr) is not None:
                if getattr(new_model, attr) != getattr(old_model, attr):
                    setattr(old_model, attr, getattr(new_model, attr))
                    old_model._dirty = True

    """
    cache clearing hook
    TODO
    """

    @classmethod
    def _clearCache(cls, models: List[TModel]) -> None:
        """
        Make deferred calls to clear caches
        Needs to save _affected_references and the dirty flag
        TODO implement this
        """
