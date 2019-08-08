from consts.district_type import DistrictType
from models.district import District
from models.event import Event
from models.match import Match
from models.team import Team
import tba_config


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
    def validate_request(cls, handler):
        kwargs = handler.request.route_kwargs
        error_dict = {'Errors': []}
        valid = True
        team_future = None
        event_future = None
        match_future = None
        district_future = None
        # Check key formats
        if 'team_key' in kwargs:
            team_key = kwargs['team_key']
            results = cls.team_id_validator(team_key)
            if results:
                error_dict['Errors'].append(results)
                valid = False
            else:
                team_future = Team.get_by_id_async(team_key)
        if 'event_key' in kwargs:
            event_key = kwargs['event_key']
            results = cls.event_id_validator(event_key)
            if results:
                error_dict['Errors'].append(results)
                valid = False
            else:
                event_future = Event.get_by_id_async(event_key)
        if 'match_key' in kwargs:
            match_key = kwargs['match_key']
            results = cls.match_id_validator(match_key)
            if results:
                error_dict['Errors'].append(results)
                valid = False
            else:
                match_future = Match.get_by_id_async(match_key)
        if 'district_key' in kwargs:
            district_key = kwargs['district_key']
            results = cls.district_id_validator(district_key)
            if results:
                error_dict['Errors'].append(results)
                valid = False
            else:
                district_future = District.get_by_id_async(district_key)
        if 'year' in kwargs:
            year = int(kwargs['year'])
            if year > tba_config.MAX_YEAR or year < tba_config.MIN_YEAR:
                error_dict['Errors'].append({'year': 'Invalid year: {}. Must be between {} and {} inclusive.'.format(year, tba_config.MIN_YEAR, tba_config.MAX_YEAR)})
                valid = False

        # Check if keys exist
        if team_future and team_future.get_result() is None:
            error_dict['Errors'].append({'team_id': 'team id {} does not exist'.format(team_key)})
            valid = False
        if event_future and event_future.get_result() is None:
            error_dict['Errors'].append({'event_id': 'event id {} does not exist'.format(event_key)})
            valid = False
        if match_future and match_future.get_result() is None:
            error_dict['Errors'].append({'match_id': 'match id {} does not exist'.format(match_key)})
            valid = False
        if district_future and district_future.get_result() is None:
            error_dict['Errors'].append({'district_id': 'district id {} does not exist'.format(district_key)})
            valid = False

        if not valid:
            return error_dict

    @classmethod
    def is_valid_model_key(cls, key):
        return (Team.validate_key_name(key) or
            Event.validate_key_name(key) or
            Match.validate_key_name(key) or
            District.validate_key_name(key))

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
        if District.validate_key_name(value) is False:
            return district_key_error
