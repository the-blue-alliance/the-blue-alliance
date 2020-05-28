from common import helpers


def RootHandler() -> str:
    return "Web says: {}".format(helpers.hello_world())
