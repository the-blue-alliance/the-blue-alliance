import abc
from typing import Dict, Generic, List, Union

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.helpers.listify import delistify, listify
from backend.common.profiler import Span
from backend.common.protocols.locatable import Locatable
from backend.common.queries.types import DictQueryReturn, QueryReturn


class ConverterBase(abc.ABC, Generic[QueryReturn, DictQueryReturn]):
    # Used to version cached outputs
    SUBVERSIONS: Dict[ApiMajorVersion, int]

    _query_return: QueryReturn

    def __init__(self, query_return: QueryReturn):
        self._query_return = query_return

    def convert(
        self, version: ApiMajorVersion
    ) -> Union[None, DictQueryReturn, List[DictQueryReturn]]:
        with Span("{}.convert".format(self.__class__.__name__)):
            if self._query_return is None:
                return None
            converted_query_return = self._convert_list(
                listify(self._query_return), version
            )
            if isinstance(self._query_return, list):
                return converted_query_return
            else:
                return delistify(converted_query_return)

    @classmethod
    @abc.abstractmethod
    def _convert_list(
        cls, model_list: List, version: ApiMajorVersion
    ) -> List[DictQueryReturn]:
        return [{} for model in model_list]

    @classmethod
    def constructLocation_v3(cls, model: Locatable) -> Dict:
        """
        Works for teams and events
        """
        return {
            "city": model.city or (model.nl and model.nl.city),
            "state_prov": model.state_prov or (model.nl and model.nl.state_prov_short),
            "country": model.country or (model.nl and model.nl.country_short_if_usa),
            "postal_code": model.postalcode or (model.nl and model.nl.postal_code),
            "lat": None,
            "lng": None,
            "location_name": model.nl and model.nl.name,
            "address": model.nl and model.nl.formatted_address,
            "gmaps_place_id": None,
            "gmaps_url": None,
        }
