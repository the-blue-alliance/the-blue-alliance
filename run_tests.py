#!/usr/bin/python
import multiprocessing
import optparse
import StringIO
import sys
import time
import warnings

# Install the Python unittest2 package before you run this script.
import unittest2

USAGE = """%prog -s SDK_PATH -t TEST_PATTERN
Run unit tests for App Engine apps.
The SDK Path is probably /usr/local/google_appengine on Mac OS

SDK_PATH    Path to the SDK installation"""


sys.path.insert(1, 'lib')


def main(sdk_path, test_pattern):
    start_time = time.time()

    sys.path.insert(0, sdk_path)
    import dev_appserver
    dev_appserver.fix_sys_path()

    suite = unittest2.loader.TestLoader().discover("tests", test_pattern)
    tests = unittest2.TextTestRunner(verbosity=2).run(suite)

    if tests.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    parser = optparse.OptionParser(USAGE)

    parser.add_option("-s", "--sdk_path", type="string", default="/usr/local/google_appengine",
                      help="path to load Google Appengine SDK from")
    parser.add_option("-t", "--test_pattern", type="string", default="test*.py",
                      help="pattern for tests to run")
    options, args = parser.parse_args()

    main(options.sdk_path, options.test_pattern)
