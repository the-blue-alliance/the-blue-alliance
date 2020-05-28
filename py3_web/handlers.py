from common import test


def RootHandler():
    return "Web says: {}".format(test.hello_world())
