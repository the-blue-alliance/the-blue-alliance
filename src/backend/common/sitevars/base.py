import abc
import json
from typing import Callable, Generic, TypeVar

from backend.common.models.sitevar import Sitevar

SVType = TypeVar("SVType")


class SitevarBase(abc.ABC, Generic[SVType]):
    @staticmethod
    @abc.abstractmethod
    def key() -> str:
        ...

    @staticmethod
    @abc.abstractmethod
    def default_value() -> SVType:
        ...

    @classmethod
    def _fetch_sitevar(cls) -> Sitevar:
        return Sitevar.get_or_insert(
            cls.key(), values_json=json.dumps(cls.default_value())
        )

    @classmethod
    def get(cls) -> SVType:
        sitevar = cls._fetch_sitevar()
        return sitevar.contents

    @classmethod
    def put(cls, val: SVType) -> None:
        cls.update(
            should_update=lambda _: True,
            update_f=lambda _: val,
        )

    @classmethod
    def update(
        cls,
        should_update: Callable[[SVType], bool],
        update_f: Callable[[SVType], SVType],
    ) -> None:
        sitevar = cls._fetch_sitevar()
        val: SVType = sitevar.contents
        if not should_update(val):
            return

        new_val = update_f(val)
        sitevar.contents = new_val
        sitevar.put()
