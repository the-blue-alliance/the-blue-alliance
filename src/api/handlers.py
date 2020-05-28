from common import helpers


def RootHandler(path):
    return "API says: {}".format(helpers.hello_world())
