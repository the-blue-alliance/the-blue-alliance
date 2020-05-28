from database.dict_converters.converter_base import ConverterBase


class TeamConverter(ConverterBase):
    SUBVERSIONS = {  # Increment every time a change to the dict is made
        3: 4,
    }

    @classmethod
    def _convert(cls, teams, dict_version):
        CONVERTERS = {
            3: cls.teamsConverter_v3,
        }
        return CONVERTERS[dict_version](teams)

    @classmethod
    def teamsConverter_v3(cls, teams):
        return map(cls.teamConverter_v3, teams)

    @classmethod
    def teamConverter_v3(cls, team):
        has_nl = team.nl and team.nl.city and team.nl.state_prov and team.nl.country
        default_name = "Team {}".format(team.team_number)
        team_dict = {
            'key': team.key.id(),
            'team_number': team.team_number,
            'nickname': team.nickname if team.nickname else default_name,
            'name': team.name if team.name else default_name,
            'website': team.website,
            'rookie_year': team.rookie_year,
            'motto': None,
            'home_championship': team.championship_location,
            'school_name': team.school_name,
        }
        team_dict.update(cls.constructLocation_v3(team))
        return team_dict
