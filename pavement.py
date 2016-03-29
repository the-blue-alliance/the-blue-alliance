# Easy paver commands for less command typing and more coding.
# Visit http://paver.github.com/paver/ to get started. - @brandondean Sept. 30
import subprocess
import json
import time
from paver.easy import *

path = path("./")


@task
@consume_args
def deploy(args):
    sh("python deploy.py " + " ".join(args))


@task
def javascript():
    """Combine Compress Javascript"""
    print("Combining and Compressing Javascript")
    sh("python do_compress.py js")


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
    test_function([])
    make()


@task
def setup():
    """Set up for development environments."""
    setup_function()


@task
@consume_args
def test(args):
    """Run tests. Accepts an argument to match subnames of tests"""
    test_function(args)


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


def setup_function():
    make()


def test_function(args):
    print("Running Tests")

    test_pattern = ""
    if len(args) > 0:
        test_pattern = " --test_pattern=*%s*" % args[0]

    sh("python run_tests.py%s 2> test_failures.temp" % test_pattern)
