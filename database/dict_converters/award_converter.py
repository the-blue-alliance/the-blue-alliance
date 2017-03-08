from database.dict_converters.converter_base import ConverterBase


class AwardConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 3,
    }

    @classmethod
    def _convert(cls, awards, dict_version):
        AWARD_CONVERTERS = {
            3: cls.awardsConverter_v3,
        }
        return AWARD_CONVERTERS[dict_version](awards)

    @classmethod
    def awardsConverter_v3(cls, awards):
        awards = map(cls.awardConverter_v3, awards)
        return awards

    @classmethod
    def awardConverter_v3(cls, award):
        recipient_list_fixed = []
        for recipient in award.recipient_list:
            recipient_list_fixed.append({
                'awardee': recipient['awardee'],
                'team_key': 'frc{}'.format(recipient['team_number']) if recipient['team_number'] else None,
            })
        return {
            'name': award.name_str,
            'award_type': award.award_type_enum,
            'year': award.year,
            'event_key': award.event.id(),
            'recipient_list': recipient_list_fixed,
        }
