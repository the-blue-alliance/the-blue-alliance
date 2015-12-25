"""
To use:
1. Clone a production copy of TBA in the same directory as the development copy by running: `git clone git@github.com:the-blue-alliance/the-blue-alliance.git the-blue-alliance-prod`
2. Ensure APP_CFG_DIR points to the correct location
"""

import os
import sys


APP_CFG_DIR = '~/Downloads/google_appengine/appcfg.py'


def main(argv):
    skip_tests = '-s' in argv

    os.chdir('../the-blue-alliance-prod')
    os.system('git pull origin master')

    test_status = 0
    if skip_tests:
        print "Skipping tests!"
        os.system('paver make')
    else:
        test_status = os.system('paver preflight')

    if test_status == 0:
        # Update default module and other YAMLs
        os.system('python ' + APP_CFG_DIR + ' -A tbatv-prod-hrd update .')
        # Update other modules
        os.system('python ' + APP_CFG_DIR + ' -A tbatv-prod-hrd update app-backend-tasks.yaml')
    else:
        print "Tests failed! Did not deploy."

if __name__ == "__main__":
    main(sys.argv[1:])
