#!/usr/bin/python
import multiprocessing
import optparse
import StringIO
import os
import random
import string
import sys
import time
import logging

# Install the Python unittest2 package before you run this script.
import unittest2

USAGE = """%prog -s SDK_PATH -t TEST_PATTERN
Run unit tests for App Engine apps.
The SDK Path is probably /usr/local/google_appengine on Mac OS

SDK_PATH    Path to the SDK installation"""


sys.path.insert(1, 'lib')
MULTITHREAD = True
MAX_JOBS = 4


def proc_init(l, fail, total):
    global lock
    global fail_count
    global total_run
    lock = l
    fail_count = fail
    total_run = total


def run_suite(suite):
    sio = StringIO.StringIO()
    testresult = unittest2.TextTestRunner(sio, verbosity=2).run(suite)
    output = sio.getvalue()
    with lock:
        total_run.value += testresult.testsRun
        if not testresult.wasSuccessful():
            fail_count.value += 1
        print output.encode('utf-8')


def main(sdk_path, test_pattern):
    logging.disable(logging.WARNING)

    start_time = time.time()

    os.environ['IS_TBA_TEST'] = "true"

    sys.path.insert(0, sdk_path)
    import dev_appserver
    dev_appserver.fix_sys_path()

    # Set up custom django template filters
    from google.appengine.ext.webapp import template
    template.register_template_library('common.my_filters')

    suites = unittest2.loader.TestLoader().discover("tests", test_pattern)

    fail = False
    total_tests_run = 0
    if MULTITHREAD:
        proc_lock = multiprocessing.Lock()
        fail_count = multiprocessing.Value('i', 0)
        total_run = multiprocessing.Value('i', 0)
        pool = multiprocessing.Pool(MAX_JOBS, initializer=proc_init, initargs=(proc_lock, fail_count, total_run,))
        pool.map(run_suite, suites)
        pool.close()
        pool.join()

        fail = fail_count.value > 0
        total_tests_run = total_run.value
    else:
        result_queue = multiprocessing.Queue()
        for suite in suites:
            sio = StringIO.StringIO()
            testresult = unittest2.TextTestRunner(sio, verbosity=2).run(suite)
            result_queue.put((testresult.testsRun, testresult.wasSuccessful()))
            print '-----------------------'
            print sio.getvalue().encode('utf-8')

        while not result_queue.empty():
            tests_run, was_successful = result_queue.get()
            total_tests_run += tests_run
            if not was_successful:
                fail = True

    os.unsetenv('IS_TBA_TEST')
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

    parser.add_option("-s", "--sdk_path", type="string", default="/google_appengine",
                      help="path to load Google Appengine SDK from")
    parser.add_option("-t", "--test_pattern", type="string", default="test*.py",
                      help="pattern for tests to run")
    options, args = parser.parse_args()

    main(options.sdk_path, options.test_pattern)
