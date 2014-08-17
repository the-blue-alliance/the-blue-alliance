from consts.district_type import DistrictType
from models.event import Event
from models.match import Match
from models.team import Team


class ValidationHelper(object):
    """
    A collection of methods to validate model ids and return standard
    error messages if they are invalid.
    """

    @classmethod
    def validate(cls, validators):
        """
        Takes a list of tuples that defines a call to a validator
        (ie team_id_validator) and it's corresponding value to validate.
        Returns a dictionary of error messages if invalid.
        Example: ValidationHelper.validate([('team_id_validator', 'frc101')])
        """

        error_dict = { "Errors": list() }
        valid = True
        for v in validators:
            results = getattr(ValidationHelper, v[0])(v[1])
            if results:
                error_dict["Errors"].append(results)
                valid = False

        if valid is False:
            return error_dict

    @classmethod
    def team_id_validator(cls, value):
        error_message = "{} is not a valid team id".format(value)
        team_key_error = { "team_id": error_message}
        if Team.validate_key_name(value) is False:
            return team_key_error

    @classmethod
    def event_id_validator(cls, value):
        error_message = "{} is not a valid event id".format(value)
        event_key_error = { "event_id": error_message}
        if Event.validate_key_name(value) is False:
            return event_key_error

    @classmethod
    def match_id_validator(cls, value):
        error_message = "{} is not a valid match id".format(value)
        match_key_error = { "match_id": error_message}
        if Match.validate_key_name(value) is False:
            return match_key_error

    @classmethod
    def district_id_validator(cls, value):
        error_message = "{} is not a valid district abbreviation".format(value)
        district_key_error = {"district_abbrev": error_message}
        if not value in DistrictType.abbrevs:
            return district_key_error
