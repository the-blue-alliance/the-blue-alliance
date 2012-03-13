# Uses the gdata api available at:
# http://code.google.com/p/gdata-python-client/downloads/list

import gdata.spreadsheet.service

# Change these values
user = "example@gmail.com"
passwd = "password"
key = "0ApRO2Yzh2z01dExFZEdieV9WdTJsZ25HSWI3VUxsWGc" # key for Greg's spreadsheet
worksheet_id = "2" # worksheets are numbered from 0, so 1 represents worksheet 2

# Create a client class which will make HTTP requests with Google Docs server.
client = gdata.spreadsheet.service.SpreadsheetsService()
client.email = user
client.password = passwd
client.source = "The Blue Alliance"
client.ProgrammaticLogin()

feed = client.GetListFeed(key, worksheet_id)

# The following is based upon SpreadSheetExample.py that came with the gdata python client
# Modify this so that YoutubeVideo objects are made instead of printing the data

# Get rid of rows without an event code
for i, entry in enumerate(list(feed.entry)):
  for key in entry.custom:
    if (key=="event") and (entry.custom[key].text is None):
      feed.entry.remove(entry)
      
for i, entry in enumerate(feed.entry):
  if isinstance(feed, gdata.spreadsheet.SpreadsheetsCellsFeed):
    print '%s %s\n' % (entry.title.text, entry.content.text)
  elif isinstance(feed, gdata.spreadsheet.SpreadsheetsListFeed):
    print '%s %s %s' % (i, entry.title.text, entry.content.text)
     #Print this row's value for each column (the custom dictionary is
     #built using the gsx: elements in the entry.)
    print 'Contents:'
    for key in entry.custom:
      print '  %s: %s' % (key, entry.custom[key].text) # here is the data we want
    print '\n',
  else:
    print '%s %s\n' % (i, entry.title.text)

