"""
Provides helper functions to assist with bulkloader.yaml
"""


def fix_json(x):
    """
    Replace single quotes in JSON with double quotes.
    """
    if len(x) > 0:
        return str(x).replace("\'", "\"")
    else:
        return None


def fix_list(x):
    """
    Turn a string of a list into a Python list.
    """
    if len(x) > 0:
        y = eval(x)
        if len(y) > 0:
            return y

    return None
