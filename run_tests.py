#!/usr/bin/python
import multiprocessing
import optparse
import StringIO
import sys
import time
import warnings

# Install the Python unittest2 package before you run this script.
import unittest2

USAGE = """%prog SDK_PATH
Run unit tests for App Engine apps.
The SDK Path is probably /usr/local/google_appengine on Mac OS

SDK_PATH    Path to the SDK installation"""


def start_suite(suite, queue):
    sio = StringIO.StringIO()
    testresult = unittest2.TextTestRunner(sio, verbosity=2).run(suite)
    queue.put((sio.getvalue(), testresult.testsRun, testresult.wasSuccessful()))


def main(sdk_path, test_pattern):
    start_time = time.time()

    sys.path.insert(0, sdk_path)
    import dev_appserver
    dev_appserver.fix_sys_path()

    suites = unittest2.loader.TestLoader().discover("tests", test_pattern)

    processes = []
    result_queue = multiprocessing.Queue()
    for suite in suites:
        process = multiprocessing.Process(target=start_suite, args=[suite, result_queue])
        process.start()
        processes.append(process)

    for process in processes:
        process.join()

    fail = False
    total_tests_run = 0
    while not result_queue.empty():
        test_output, tests_run, was_successful = result_queue.get()
        total_tests_run += tests_run
        print '-----------------------'
        print test_output
        if not was_successful:
            fail = True

    print "================================"
    print "Completed {} tests in: {} seconds".format(total_tests_run, time.time() - start_time)
    if fail:
        print "TESTS FAILED!"
    else:
        print "TESTS PASSED!"
    print "================================"
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
