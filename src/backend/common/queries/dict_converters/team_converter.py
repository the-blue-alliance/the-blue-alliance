from backend.common.queries.dict_converters.converter_base import ConverterBase


class TeamConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 4,
    }

    @classmethod
    def _convert(cls, teams, version):
        CONVERTERS = {
            3: cls.teamsConverter_v3,
        }
        return CONVERTERS[version](teams)

    @classmethod
    def teamsConverter_v3(cls, teams):
        return list(map(cls.teamConverter_v3, teams))

    @classmethod
    def teamConverter_v3(cls, team):
        default_name = "Team {}".format(team.team_number)
        team_dict = {
            "key": team.key.id(),
            "team_number": team.team_number,
            "nickname": team.nickname if team.nickname else default_name,
            "name": team.name if team.name else default_name,
            "website": team.website,
            "rookie_year": team.rookie_year,
            "motto": None,
            # "home_championship": team.championship_location,  # TODO: event not ported yet
            "school_name": team.school_name,
        }
        team_dict.update(cls.constructLocation_v3(team))
        return team_dict
