"""
To use:
1. Clone a production copy of TBA in the same directory as the development copy by running: `git clone git@github.com:the-blue-alliance/the-blue-alliance.git the-blue-alliance-prod`
2. Ensure APP_CFG_DIR points to the correct location
"""

import argparse
import os
import sys


APP_CFG_DIR = '~/Downloads/google_appengine' # Eugene's Windows
# APP_CFG_DIR = '/usr/local/bin' # Mac OS symlinks made by GoogleAppEngineLauncher


def main():
    parser = argparse.ArgumentParser(description='Deploy The Blue Alliance app.')
    parser.add_argument('app_cfg_dir', type=str, default=APP_CFG_DIR,
                        help='path to folder containing appcfg.py')
    parser.add_argument('-s', '--skip_tests', action='store_true',
                        help='Skip running tests. #yolo.')
    args = parser.parse_args()

    os.chdir('../the-blue-alliance-prod')
    os.system('git pull origin master')

    test_status = 0
    if args.skip_tests:
        print "Skipping tests!"
        os.system('paver make')
    else:
        test_status = os.system('paver preflight')

    if test_status == 0:
        # Update default module and other YAMLs
        os.system('python ' + args.app_cfg_dir + '/appcfg.py -A tbatv-prod-hrd update .')
        # Update other modules
        os.system('python ' + args.app_cfg_dir + '/appcfg.py -A tbatv-prod-hrd update app-backend-tasks.yaml')
        os.system('python ' + args.app_cfg_dir + '/appcfg.py -A tbatv-prod-hrd update app-backend-tasks-b2.yaml')
    else:
        print "Tests failed! Did not deploy."

if __name__ == "__main__":
    main()
