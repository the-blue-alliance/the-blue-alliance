from typing import Dict, List, NewType, Optional

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.event_predictions_v2 import EventPredictionsV2
from backend.common.queries.dict_converters.converter_base import ConverterBase

EventPredictionsV2Dict = NewType("EventPredictionsV2Dict", Dict)


class EventPredictionsV2Converter(ConverterBase):
    SUBVERSIONS = {
        ApiMajorVersion.API_V3: 1,
    }

    @classmethod
    def _convert_list(
        cls, model_list: List[Optional[EventPredictionsV2]], version: ApiMajorVersion
    ) -> List[Optional[EventPredictionsV2Dict]]:
        CONVERTERS = {
            ApiMajorVersion.API_V3: cls.eventPredictionsV2Converter_v3,
        }
        return CONVERTERS[version](model_list)

    @classmethod
    def eventPredictionsV2Converter_v3(
        cls, event_predictions_list: List[Optional[EventPredictionsV2]]
    ) -> List[Optional[EventPredictionsV2Dict]]:
        out: List[Optional[EventPredictionsV2Dict]] = []
        for ep in event_predictions_list:
            if ep is None:
                out.append(None)
            else:
                out.append(ep.predictions)  # type: ignore
        return out
