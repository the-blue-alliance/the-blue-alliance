# Easy paver commands for less command typing and more coding.
# Visit http://paver.github.com/paver/ to get started. - @brandondean Sept. 30
import subprocess
import json
import time
from paver.easy import *

path = path("./")

@task
def clean():
  """Get rid of junk files."""

  if path.files("bulkloader-*"):
    sh("rm bulkloader-*")
    print("All cleaned up!")
  else:
    print("Nothing to clean! :)")

@task
def setup():
  """Set up data for development environments."""
  
  print("Building CSS/JS...")
  less()
  javascript()
  
  print("Setting up dev data.")
  
  print("Getting Teams")
  sh("curl -s http://localhost:8088/tasks/get/fms_team_list")
  print("Importing test Event data")
  sh("echo \"omgrobots\" | appcfg.py upload_data --config_file=bulkloader.yaml --filename=test_data/events.csv --kind=Event --url=http://localhost:8088/_ah/remote_api --num_threads=1 --email=admin@localhost --passin")
  print("Importing test Match data")
  sh("echo \"omgrobots\" | appcfg.py upload_data --config_file=bulkloader.yaml --filename=test_data/matches_2010cmp.csv --kind=Match --url=http://localhost:8088/_ah/remote_api --num_threads=1 --email=admin@localhost --passin")
  print("Enqueuing building EventTeams")
  sh("curl -s http://localhost:8088/tasks/math/enqueue/eventteam_update")
  print("Getting 2010cmp videos from TBA")
  sh("curl -s http://localhost:8088/tasks/math/do/tba_videos/2010cmp")
  print("Getting 2013 Event List")
  sh("curl -s http://localhost:8088/tasks/get/usfirst_event_list/2013")

  clean()
  print("Done setting up! 2013 events loaded and 2010cmp is now ready for testing.")

@task
def test():
  """Run tests."""
  print("Running Tests")
  sh("python run_tests.py")

@task
def test_fast():
  """Run tests that don't require HTTP"""
  print("Running Fast Tests")
  sh("python run_tests.py /usr/local/google_appengine test_math_*.py")
  sh("python run_tests.py /usr/local/google_appengine test_*parser.py")
  sh("python run_tests.py /usr/local/google_appengine test_*manipulator.py")
  sh("python run_tests.py /usr/local/google_appengine test_*api.py")
  sh("python run_tests.py /usr/local/google_appengine test_event.py")
  sh("python run_tests.py /usr/local/google_appengine test_match_cleanup.py")

@task
def less():
  """Build and Combine CSS"""
  print("Building and Combining CSS")
  sh("lessc static/css/less_css/tba_style.main.less static/css/less_css/tba_style.main.css")
  sh("lessc static/css/less_css/tba_style.gameday.less static/css/less_css/tba_style.gameday.css")
  sh("python do_compress.py css")

@task
def javascript():
    """Combine Compress Javascript"""
    print("Combining and Compressing Javascript")
    sh("python do_compress.py js")

@task
def preflight():
  """Prep a prod push"""
  test()
  less()
  javascript()

  git_branch_name = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
  git_last_commit = subprocess.check_output(["git", "log", "-1"])
  build_time = time.ctime()
  data = {'git_branch_name': git_branch_name,
          'git_last_commit': git_last_commit,
          'build_time': build_time}
  with open('version_info.json', 'w') as f:
      f.write(json.dumps(data))

@task
def lint():
  sh("python linter.py")
