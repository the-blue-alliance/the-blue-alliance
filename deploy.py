"""
To use:
1. Clone a production copy of TBA in the same directory as the development copy by running: `git clone git@github.com:the-blue-alliance/the-blue-alliance.git the-blue-alliance-prod`
2. Change the application ID in ../the-blue-alliance-prod/app.yaml from "tbatv-dev-hrd" to "tbatv-prod-hrd"
3. Ensure line 31 of this file points to the correct location

Warning: If you CTRL-c out of this script between lines 18 and 20, make sure the application ID in ../the-blue-alliance-prod/app.yaml is still correct.
"""

import os
import sys


def main(argv):
    skip_tests = '-s' in argv

    os.chdir('../the-blue-alliance-prod')
    os.system('git stash')  # undoes the application ID change to app.yaml
    os.system('git pull origin master')
    os.system('git stash pop')  # restores the application ID change to app.yaml

    test_status = 0
    if skip_tests:
        print "Skipping tests!"
        os.system('paver make')
    else:
        test_status = os.system('paver preflight')
    os.chdir('../')

    if test_status == 0:
        os.system('python ~/Downloads/google_appengine/appcfg.py --oauth2 update the-blue-alliance-prod/')
    else:
        print "Tests failed! Did not deploy."

if __name__ == "__main__":
    main(sys.argv[1:])
