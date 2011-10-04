# Easy paver commands for less command typing and more coding.
# Visit http://paver.github.com/paver/ to get started. - @brandondean Sept. 30
from paver.easy import *


path = path("./")
@task
def clean():

  if path.files("bulkloader-*"):
    sh("rm bulkloader-*")
    print "All cleaned up!"
  else:
    print "Nothing to clean! :)"
  
