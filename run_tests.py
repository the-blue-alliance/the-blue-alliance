#!/usr/bin/python
import optparse
import sys
# Install the Python unittest2 package before you run this script.
import unittest2

USAGE = """%prog SDK_PATH
Run unit tests for App Engine apps.
The SDK Path is probably /usr/local/google_appengine on Mac OS

SDK_PATH    Path to the SDK installation"""


def main(sdk_path, test_pattern):
    sys.path.insert(0, sdk_path)
    import dev_appserver
    dev_appserver.fix_sys_path()
    
    suite = unittest2.loader.TestLoader().discover("tests", test_pattern)
    unittest2.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    parser = optparse.OptionParser(USAGE)
    options, args = parser.parse_args()
    if len(args) < 1:
        print 'Warning: Trying default SDK path.'
        sdk_path = "/usr/local/google_appengine"
    else:
        sdk_path = args[0]
    
    test_pattern = "test*.py"
    if len(args) > 1:
        test_pattern = args[1]
    
    main(sdk_path, test_pattern)