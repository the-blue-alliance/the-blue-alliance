import calendar
from typing import Dict, List, NewType

from backend.common.consts.api_version import ApiMajorVersion
from backend.common.models.event_predictions_v2 import EventPredictionsV2
from backend.common.queries.dict_converters.converter_base import ConverterBase

EventPredictionsV2Dict = NewType("EventPredictionsV2Dict", Dict)


class EventPredictionsV2Converter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        ApiMajorVersion.API_V3: 0,
    }

    @classmethod
    def _convert_list(
        cls, model_list: List[EventPredictionsV2], version: ApiMajorVersion
    ) -> List[EventPredictionsV2Dict]:
        CONVERTERS = {
            3: cls.eventPredictionsV2Converter_v3,
        }
        return [CONVERTERS[version](m) for m in model_list]

    @classmethod
    def eventPredictionsV2Converter_v3(
        cls, predictions: EventPredictionsV2
    ) -> EventPredictionsV2Dict:
        return EventPredictionsV2Dict(
            {
                "event_key": predictions.key_name,
                "model_version": predictions.model_version,
                "forecast_only": bool(predictions.forecast_only),
                "last_updated": (
                    calendar.timegm(predictions.updated.utctimetuple())
                    if predictions.updated
                    else None
                ),
                "matches": predictions.matches or {},
            }
        )
