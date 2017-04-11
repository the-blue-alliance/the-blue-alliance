# Easy paver commands for less command typing and more coding.
# Visit http://paver.github.com/paver/ to get started. - @brandondean Sept. 30
import subprocess
import json
import time
import optparse
from paver.easy import *

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
def lint():
    sh("python linter.py")


@task
def make():
    javascript()
    gulp()
    less()
    jinja2()

    git_branch_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    git_last_commit = subprocess.check_output(["git", "log", "-1"])
    build_time = time.ctime()
    data = {"git_branch_name": git_branch_name,
            "git_last_commit": git_last_commit,
            "build_time": build_time}
    with open("version_info.json", "w") as f:
        f.write(json.dumps(data))


@task
def preflight():
    """Prep a prod push"""
    install_libs()
    test_function([])
    make()


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
    optparse.make_option("--port", type=int, help="Local port running the API server", default=41017),
])
def bootstrap(options):
    """Download and import an event or team from apiv3"""
    key = options.bootstrap.key
    if options.bootstrap.project:
        url = "https://{}.appspot.com".format(options.bootstrap.project)
    else:
        url = "localhost:{}".format(options.bootstrap.port)
    args = ["python", "bootstrap.py", "--url", url, key]
    print "Running {}".format(subprocess.list2cmdline(args))
    subprocess.call(args)


def test_function(args):
    print("Running Tests")

    test_pattern = ""
    if len(args) > 0:
        test_pattern = " --test_pattern=*%s*" % args[0]

    sh("python run_tests.py%s 2> test_failures.temp" % test_pattern)
