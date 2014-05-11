#!/usr/bin/python
import multiprocessing
import optparse
import sys
import warnings

# Install the Python unittest2 package before you run this script.
import unittest2

USAGE = """%prog SDK_PATH
Run unit tests for App Engine apps.
The SDK Path is probably /usr/local/google_appengine on Mac OS

SDK_PATH    Path to the SDK installation"""

RESULT_QUEUE = multiprocessing.Queue()


def start_suite(suite):
    testresult = unittest2.TextTestRunner(verbosity=2).run(suite)

    test_names = []
    for sub in suite:
        for test in sub:
            test_names.append(str(test))
    RESULT_QUEUE.put((test_names, testresult))


def main(sdk_path, test_pattern):
    sys.path.insert(0, sdk_path)
    import dev_appserver
    dev_appserver.fix_sys_path()

    suites = unittest2.loader.TestLoader().discover("tests", test_pattern)

    processes = []
    for suite in suites:
        process = multiprocessing.Process(target=start_suite, args=[suite])
        process.start()
        processes.append(process)

    for process in processes:
        process.join()

    fail = False
    while not RESULT_QUEUE.empty():
        test_names, suite_result = RESULT_QUEUE.get()
        print '-----------------------'
        for test_name in test_names:
            print test_name
        if suite_result.wasSuccessful():
            print "PASS"
        else:
            print "FAIL"
            fail = True

    print "============="
    if fail:
        print "TESTS FAILED!"
    else:
        print "TESTS PASSED!"
    print "============="
    if fail:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    parser = optparse.OptionParser(USAGE)

    parser.add_option("-s", "--sdk_path", type="string", default="/usr/local/google_appengine",
                      help="path to load Google Appengine SDK from")
    parser.add_option("-t", "--test_pattern", type="string", default="test*.py",
                      help="pattern for tests to run")
    options, args = parser.parse_args()

    main(options.sdk_path, options.test_pattern)
