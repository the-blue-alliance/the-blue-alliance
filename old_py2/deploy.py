"""
To use:
1. Clone a production copy of TBA in the same directory as the development copy by running: `git clone git@github.com:the-blue-alliance/the-blue-alliance.git the-blue-alliance-prod`
2. Ensure you have gcloud available and in your PATH (https://cloud.google.com/sdk/gcloud/)
3. If you want to allow travis support, be sure you have the official client installed and in your PATH (https://github.com/travis-ci/travis.rb)

NOTE: if your deployments are slow, try exporting the environment variable CLOUDSDK_APP_USE_GSUTIL=1 to use a different approach
"""

import argparse
import os
import time
import subprocess
import re


def main():
    parser = argparse.ArgumentParser(description='Deploy The Blue Alliance app.')
    parser.add_argument('--project', default='tbatv-prod-hrd', help="App Engine project to deploy")
    parser.add_argument('--yolo', action="store_true", help="Do not wait for travis builds to succeed #yolo", default=False)
    parser.add_argument('--config', help="gcloud configuration profile to use", default="")
    parser.add_argument('--version', help="Version for app engine modules", default="prod-1")
    parser.add_argument('--modules', help="Modules to deploy, comma separated, as yaml spec files in this directory", default="")
    parser.add_argument('--skip-cron', action="store_true", help="Do not deploy cron.yaml", default=False)
    parser.add_argument('--app-cfg-dir', help="Location of appcfg.py [deprecated]", default="")
    args = parser.parse_args()

    os.chdir('../the-blue-alliance-prod')
    os.system('git stash')
    os.system('git pull origin master')
    os.system('git stash pop')

    test_status = 0
    if args.yolo:
        print "Skipping tests!"
        print "Welcome to clowntown..."
        os.system('paver install_libs')
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
        print "Deploying..."
        os.system("gcloud version")
        cmd = ["gcloud", "app", "deploy", "--verbosity", "info", "--project", args.project]
        # appcfg.py --no_cookies -A tbatv-prod-hrd -V prod-1 update .
        appcfg_cmd = ["{}/appcfg.py".format(args.app_cfg_dir), "--no_cookies", "-A", args.project]
        if args.config:
            cmd.extend(["--configuration", args.config])
        if args.version:
            cmd.extend(["--version", args.version])
            appcfg_cmd.extend(["-V", args.version])
        if args.modules:
            modules = args.modules.split(",")
        else:
            # Full deploy
            modules = ["app.yaml", "app-backend-tasks-b2.yaml", "app-backend-tasks.yaml", "cron.yaml", "dispatch.yaml", "index.yaml", "queue.yaml"]
        if args.skip_cron and "cron.yaml" in modules:
            modules.remove("cron.yaml")
        cmd.extend(modules)
        appcfg_cmd.append("update")
        appcfg_cmd.extend(modules)
        cmd_str = subprocess.list2cmdline(appcfg_cmd if args.app_cfg_dir else cmd)
        print "Running {}".format(cmd_str)
        os.system(cmd_str)
    else:
        print "Tests failed! Did not deploy."

if __name__ == "__main__":
    main()
