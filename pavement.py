# Easy paver commands for less command typing and more coding.
# Visit http://paver.github.com/paver/ to get started. - @brandondean Sept. 30
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
def secrets():
  """Copy prod secrets over repository secrets."""
  print("Copying secrets.")
  print("Facebook")
  sh("cat secrets/facebook_prod.json > secrets/facebook.json")
  print("Twitter")
  sh("cat secrets/twitter_prod.json > secrets/twitter.json")

@task
def setup():
  """Set up data for development environments."""
  
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

  clean()
  print("Done setting up! 2010cmp is now ready for testing.")

@task
def test():
  """Run tests."""
  print("Running Tests")
  sh("python run_tests.py")

@task
def test_fast():
  """Run tests that don't require HTTP"""
  print("Running Fast Tests")
  sh("python run_tests.py /usr/local/google_appengine test_*parser.py")
  sh("python run_tests.py /usr/local/google_appengine test_*manipulator.py")
  sh("python run_tests.py /usr/local/google_appengine test_*api.py")

@task
def less():
  """Build CSS."""
  print("Building CSS")
  sh("lessc static/css/style.less static/css/style.css --yui-compress")

@task
def preflight():
  """Prep a prod push"""
  test()
  less()
  secrets()
