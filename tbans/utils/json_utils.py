import json


def json_string_to_dict(content):
    """
    Attempt to convert a JSON string to a dict.

    Args:
        content (string): JSON string to parse to a dictionary.

    Returns:
        dict: Dictionary from parsed string.
    """
    try:
        response_json = json.loads(content)
        if isinstance(response_json, dict):
            return response_json
        else:
            return {}
    except ValueError:
        return {}
    except TypeError:
        return {}
