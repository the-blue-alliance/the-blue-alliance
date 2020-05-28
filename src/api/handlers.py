from common import test


def RootHandler(path):
    return "API says: {}".format(test.hello_world())
