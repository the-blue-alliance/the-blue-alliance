"""
To use:
1. Clone a production copy of TBA in the same directory as the development copy by running: `git clone git@github.com:the-blue-alliance/the-blue-alliance.git the-blue-alliance-prod`
2. Ensure APP_CFG_DIR points to the correct location
3. If you want to allow travis support, be sure you have the official client installed and in your PATH (https://github.com/travis-ci/travis.rb)
"""

import argparse
import os
import sys
import subprocess
import re


APP_CFG_DIR = '~/Downloads/google_appengine'  # Eugene's Windows
# APP_CFG_DIR = '/usr/local/bin' # Mac OS symlinks made by GoogleAppEngineLauncher


def main():
    parser = argparse.ArgumentParser(description='Deploy The Blue Alliance app.')
    parser.add_argument('--app_cfg_dir', type=str, default=APP_CFG_DIR,
                        help='path to folder containing appcfg.py')
    parser.add_argument('--project', default='tbatv-prod-hrd', help="App Engine project to deploy")
    parser.add_argument('--reauth', action="store_true", help="Prompt for reauth during GAE commands", default=False)
    parser.add_argument('--yolo', action="store_true", help="Do not wait for travis builds to succeed #yolo", default=False)
    args = parser.parse_args()

    os.chdir('../the-blue-alliance-prod')
    os.system('git pull origin master')

    test_status = 0
    if args.yolo:
        print "Skipping tests!"
        print "Welcome to clowntown..."
        os.system('paver make')
    else:
        test_status = os.system('paver preflight')
        print "Verifying travis build for branch master"
        status = "created"
        duration = ""
        while status == "created" or status == "started":
            try:
                info = subprocess.check_output(["travis", "show", "master"])
            except subprocess.CalledProcessError:
                try:
                    input("Error getting travis status. Press Enter to continue...")
                except SyntaxError:
                    pass
            regex = re.search(".*State:[ \t]+((\w)*)\n", info)
            status = regex.group(1)
            regex = re.search(".*Duration:[ \t]+(([\w\d ])*)", info)
            duration = regex.group(1) if regex else None
            print "Build Status: {}, duration: {}".format(status, duration)
            if status == "passed":
                break
            elif status == "failed" or status == "errored":
                test_status = 1
                break
            time.sleep(30)

    if test_status == 0:
        other_args = "--no_cookies" if args.reauth else ""
        modules = [".", "app-backend-tasks.yaml", "app-backend-tasks-b2.yaml"]
        for module in modules:
            os.system("python {}/appcfg.py {} -A {} update {}".format(args.app_cfg_dir, other_args, args.project, module))
    else:
        print "Tests failed! Did not deploy."

if __name__ == "__main__":
    main()
