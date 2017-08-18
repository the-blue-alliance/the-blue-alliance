#!/usr/bin/python
import multiprocessing
import optparse
import StringIO
import os
import random
import string
import sys
import time
import django.conf.global_settings

# Install the Python unittest2 package before you run this script.
import unittest2

USAGE = """%prog -s SDK_PATH -t TEST_PATTERN
Run unit tests for App Engine apps.
The SDK Path is probably /usr/local/google_appengine on Mac OS

SDK_PATH    Path to the SDK installation"""


sys.path.insert(1, 'lib')
MULTITHREAD = True


def start_suite(suite, queue):
    sio = StringIO.StringIO()
    testresult = unittest2.TextTestRunner(sio, verbosity=2).run(suite)
    queue.put((sio.getvalue(), testresult.testsRun, testresult.wasSuccessful()))


def main(sdk_path, test_pattern):
    start_time = time.time()

    os.environ['IS_TBA_TEST'] = "true"

    # Fix django template loaders being messed up
    django.conf.global_settings.SECRET_KEY = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django.conf.global_settings')

    # Set up custom django template filters
    from google.appengine.ext.webapp import template
    template.register_template_library('common.my_filters')

    sys.path.insert(0, sdk_path)
    import dev_appserver
    dev_appserver.fix_sys_path()

    suites = unittest2.loader.TestLoader().discover("tests", test_pattern)

    processes = []
    result_queue = multiprocessing.Queue()
    for suite in suites:
        if MULTITHREAD:
            process = multiprocessing.Process(target=start_suite, args=[suite, result_queue])
            process.start()
            processes.append(process)
        else:
            sio = StringIO.StringIO()
            testresult = unittest2.TextTestRunner(sio, verbosity=2).run(suite)
            result_queue.put((sio.getvalue(), testresult.testsRun, testresult.wasSuccessful()))

    for process in processes:
        process.join()

    os.unsetenv('IS_TBA_TEST')
    fail = False
    total_tests_run = 0
    while not result_queue.empty():
        test_output, tests_run, was_successful = result_queue.get()
        total_tests_run += tests_run
        print '-----------------------'
        print test_output.encode('utf-8')
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
