class SubscriptionResponse(object):
    """ Base response object for Instance ID API responses. """
    def __init__(self, response=None, error=None):
        """
        Args:
            response (object, content/status_code/headers): response from urlfetch Instance ID API call (https://cloud.google.com/appengine/docs/standard/python/refdocs/google.appengine.api.urlfetch)
            error (string): Directly pass an error instead of trying to parse the error from the JSON response.
        """
        if not response and not error:
            raise ValueError('SubscriptionResponse must be initilized with either a response or an error')

        from tbans.utils.validation_utils import validate_is_string, validate_is_type

        # Check that response looks right
        if response:
            if response.content:
                validate_is_string(content=response.content)
            # Check that we have a status_code
            validate_is_type(int, not_empty=False, status_code=response.status_code)
        self._response = response

        # Check that error looks right
        if error:
            validate_is_string(error=error)
        self._error = error

    @property
    def _raw_data(self):
        from tbans.utils.json_utils import json_string_to_dict
        if self._response:
            return json_string_to_dict(self._response.content)
        return {}

    @property
    def _status_code(self):
        if self._response:
            return self._response.status_code
        return None

    @property
    def data(self):
        """
        Parsed dictionary from JSON response content.

        Note:
            Will not contain error information, as this is accessed through other methods.

        Returns:
            dict
        """
        data = self._raw_data
        # Remove error from our data JSON
        data.pop('error', None)
        return data

    @property
    def iid_error(self):
        """
        Return the IIDError for the response.

        Returns:
            string, IIDError - may be None if no error.
        """
        status_code = self._status_code
        # If we pass an error - we consider this an unknown error, since it probably wasn't caused by the IID API
        from tbans.consts.iid_error import IIDError
        if self._error:
            return IIDError.UNKNOWN_ERROR
        # If we have a non-200 error code, pull the corresponding IID Error
        elif status_code and status_code is not 200:
            return IIDError.ERROR_CODES.get(status_code, IIDError.UNKNOWN_ERROR)
        # Otherwise, no error at all
        else:
            return None

    @property
    def error(self):
        """
        Return the human-readable error for this response.

        Returns:
            string, May be None if no error.
        """
        status_code = self._status_code
        # If we pass an error - use the error string as the error
        if self._error:
            return self._error
        # If we have a non-200 error code, get the error from the JSON (if possible).
        elif status_code and status_code is not 200:
            raw_json = self._raw_data
            json_error = raw_json.pop('error', None)
            if json_error:
                return json_error
            else:
                return "Unknown error."
        # Otherwise, no error at all
        else:
            return None
