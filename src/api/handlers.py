from common import helpers


def RootHandler(path: str) -> str:
    return "API says: {}".format(helpers.hello_world())
