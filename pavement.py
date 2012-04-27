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
def dev_data_setup():
  """Set up data for development environments."""
  
  print("Setting up dev data. Just hit enter when prompted for credentials.")
  
  print("Importing test Event data")
  sh("appcfg.py upload_data --config_file=bulkloader.yaml --filename=test_data/events.csv --kind=Event --url=http://localhost:8088/_ah/remote_api")
  print("Importing test Match data")
  sh("appcfg.py upload_data --config_file=bulkloader.yaml --filename=test_data/matches_2010cmp.csv --kind=Match --url=http://localhost:8088/_ah/remote_api")
  
  clean()
  print("Done setting up!")