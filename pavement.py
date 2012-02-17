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
def dev_teams_setup():
  """Set up team data for development environments."""
  
  print("Instantiating Teams. This will take a few minutes. Watch the app log console for progress.")
  sh("wget --delete-after --quiet http://localhost:8088/tasks/usfirst_teams_instantiate?year=2012&skip=0")

@task
def dev_data_setup():
  """Set up data for development environments."""
  
  print("Setting up dev data. Just hit enter when prompted for credentials.")
  
  print("Importing test Event data")
  sh("appcfg.py upload_data --config_file=bulkloader.yaml --filename=test_data/events.csv --kind=Event --url=http://localhost:8088/_ah/remote_api")
  print("Importing test Match data")
  sh("appcfg.py upload_data --config_file=bulkloader.yaml --filename=test_data/matches_2010cmp.csv --kind=Match --url=http://localhost:8088/_ah/remote_api")
  print("Importing test YoutubeVideo data")
  sh("appcfg.py upload_data --config_file=bulkloader.yaml --filename=test_data/youtubevideos_2010cmp.csv --kind=YoutubeVideo --url=http://localhost:8088/_ah/remote_api")
  print("Updating EventTeams")
  sh("wget --delete-after --quiet http://localhost:8088/tasks/eventteam_update_enqueue")
  print("Scraping TBAVideos")
  sh("wget --delete-after --quiet http://localhost:8088/tasks/tba_videos_get/2010cmp")
  
  clean()
  print("Done setting up!")