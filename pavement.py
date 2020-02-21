# Easy paver commands for less command typing and more coding.
# Visit http://paver.github.com/paver/ to get started. - @brandondean Sept. 30
import subprocess
import sys
import json
import time
import optparse
import os
import re
from paver.easy import *
from openapi_spec_validator import validate_spec

path = path("./")


@task
@cmdopts([
    optparse.make_option("-p", "--project", help="App Engine project to deploy", default="tbatv-prod-hrd"),
    optparse.make_option("--yolo", action="store_true", help="Do not wait for the travis build to succeed #yolo", default=False),
    optparse.make_option("--config", help="gcloud SDK configuration profile to use", default=""),
    optparse.make_option("--version", help="App engine version to deploy", default=""),
    optparse.make_option("--modules", help="Comma separated names of module yaml files to deploy", default=""),
    optparse.make_option("--skip-cron", action="store_true", help="Do not deploy cron.yaml", default=False),
    optparse.make_option("--app-cfg-dir", help="Place to find appcfg.py [deprecated]", default=""),
])
def deploy(options):
    args = ["python", "deploy.py", "--project", options.deploy.project]
    if options.deploy.yolo:
        args.append("--yolo")
    if options.deploy.config:
        args.extend(["--config", options.deploy.config])
    if options.deploy.version:
        args.extend(["--version", options.deploy.version])
    if options.deploy.modules:
        args.extend(["--modules", options.deploy.modules])
    if options.skip_cron:
        args.append("--skip-cron")
    if options.app_cfg_dir:
        args.extend(["--app-cfg-dir", options.app_cfg_dir])
    print "Running {}".format(subprocess.list2cmdline(args))
    subprocess.call(args)


@task
def javascript():
    """Combine Compress Javascript"""
    print("Combining and Compressing Javascript")
    sh("python do_compress.py js")


@task
def gulp():
    """Update all npm dependencies and run 'gulp build' task"""
    print("Running 'gulp build'")
    sh("npm update && gulp build --production")


@task
def install_libs():
    sh("pip install -r deploy_requirements.txt -t lib")


@task
def jinja2():
    sh("python compile_jinja2_templates.py")


@task
def less():
    """Build and Combine CSS"""
    print("Building and Combining CSS")
    sh("lessc static/css/less_css/tba_style.main.less static/css/less_css/tba_style.main.css")
    sh("lessc static/css/less_css/tba_style.gameday.less static/css/less_css/tba_style.gameday.css")
    sh("python do_compress.py css")


@task
@cmdopts([
    ('commit=', 'c', 'Commit hash to lint'),
    ('base=', 'b', 'Lint all changes between the current HEAD and this base branch'),
])
def lint(options):
    args = ""
    if 'base' in options.lint:
        args = "--base {}".format(options.lint.base)
    elif 'commit' in options.lint:
        args = "--commit {}".format(options.lint.commit)

    sh("python ops/linter.py {}".format(args))


@task
def validate_swagger():
    dir = "./static/swagger"
    for fname in os.listdir(dir):
        print("Checking {}...".format(fname))
        if fname.endswith(".json"):
            with open('{}/{}'.format(dir, fname), 'rb') as file:
                try:
                    spec_dict = json.load(file)
                except ValueError, e:
                    print("Invalid JSON")
                    print(e)
                    sys.exit(1)
            try:
                validate_spec(spec_dict)
            except Exception, e:
                print("Invalid OpenAPI Spec")
                print(e)
                sys.exit(1)
            print("{} validated!".format(fname))
    sys.exit(0)


@task
def make():
    javascript()
    gulp()
    less()
    jinja2()

    build_time = time.ctime()
    travis_job = os.environ.get('TRAVIS_BUILD_ID', '')
    try:
        git_branch_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        git_last_commit = subprocess.check_output(["git", "log", "-1"])
    except Exception:
        print "No git history found, falling back to defaults..."
        git_branch_name = 'dev'
        git_last_commit = 'dev'
    data = {"git_branch_name": git_branch_name,
            "git_last_commit": git_last_commit,
            "build_time": build_time,
            "build_number": travis_job,
            }
    with open("version_info.json", "w") as f:
        f.write(json.dumps(data))


@task
def make_endpoints_config():
    sh("python lib/endpoints/endpointscfg.py get_openapi_spec mobile_main.MobileAPI --hostname tbatv-prod-hrd.appspot.com")
    sh("python lib/endpoints/endpointscfg.py get_openapi_spec clientapi.clientapi_service.ClientAPI --hostname tbatv-prod-hrd.appspot.com")


@task
def preflight():
    """Prep a prod push"""
    install_libs()
    test_function([])
    make()


@task
def run():
    """Run local dev server"""
    sh("dev_appserver.py dispatch.yaml app.yaml app-backend-tasks.yaml app-backend-tasks-b2.yaml api.yaml clientapi.yaml tasks.yaml")


@task
@consume_args
def test(args):
    """Run tests. Accepts an argument to match subnames of tests"""
    test_function(args)


@task
def setup():
    sh("pip install -r requirements.txt")
    install_libs()
    make()


@task
def test_fast():
    """Run tests that don't require HTTP"""
    print("Running Fast Tests")
    sh("python run_tests.py --test_pattern=test_math_*.py")
    sh("python run_tests.py --test_pattern=test_*helper*.py")
    sh("python run_tests.py --test_pattern=test_*parser*.py")
    sh("python run_tests.py --test_pattern=test_*manipulator.py")
    sh("python run_tests.py --test_pattern=test_*api.py")
    sh("python run_tests.py --test_pattern=test_event.py")
    sh("python run_tests.py --test_pattern=test_match_cleanup.py")
    sh("python run_tests.py --test_pattern=test_event_group_by_week.py")
    sh("python run_tests.py --test_pattern=test_event_team_repairer.py")
    sh("python run_tests.py --test_pattern=test_event_team_updater.py")
    sh("python run_tests.py --test_pattern=test_event_get_short_name.py")


@task
@cmdopts([
    optparse.make_option("--key", help="Event, Team, or Match key to import", default="2016necmp"),
    optparse.make_option("--project", help="App Engine Project", default=""),
    optparse.make_option("--port", type=int, help="Local port running the API server", default=None),
])
def bootstrap(options):
    """Download and import an event or team from apiv3"""
    log = '/var/log/tba.log'
    key = options.bootstrap.key
    url = None
    if options.bootstrap.project:
        url = "https://{}.appspot.com".format(options.bootstrap.project)
    elif os.path.exists(log) and os.path.isfile(log):
        prog = re.compile('Starting API server at: http://localhost:(\d{5})$')
        with open(log, 'r') as f:
            for line in f:
                result = prog.search(line.strip())
                if result:
                    url = "localhost:{}".format(result.group(1))
                    break

    if not url:
        if "port" not in options.bootstrap or not options.bootstrap.port:
            print "Unable to find GAE remote API port, either tee the log to {} or provide --port".format(log)
            return
        url = "localhost:{}".format(options.bootstrap.port)
    args = ["python", "bootstrap.py", "--url", url, key]
    print "Running {}".format(subprocess.list2cmdline(args))
    subprocess.call(args)


@task
def devserver():
    sh("dev_appserver.py --skip_sdk_update_check=true --admin_host=0.0.0.0 --host=0.0.0.0 --datastore_path=/datastore/tba.db dispatch.yaml app.yaml app-backend-tasks.yaml app-backend-tasks-b2.yaml api.yaml clientapi.yaml tasks.yaml")


def test_function(args):
    print("Running Tests")

    test_pattern = ""
    if len(args) > 0:
        test_pattern = " --test_pattern=*%s*" % args[0]

    sh("python run_tests.py%s" % test_pattern)
