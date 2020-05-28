from common import helpers


def RootHandler():
    return "Web says: {}".format(helpers.hello_world())
