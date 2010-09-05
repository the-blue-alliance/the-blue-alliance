#!/usr/bin/env python
# Requires BeautifulSoup, tested with version 3.0.8.1

import sys
import os
import urllib
import cookielib
from urllib2 import *
from BeautifulSoup import *

LOGIN_URL="%s/_ah/login?email=test%%40example.com&admin=True&action=Login&continue="
TASKS_URL='%s/_ah/admin/tasks'
class CApp(object):
  def __init__(self, options):
    self.options = options
    self.url = 'http://%s:%s' % (options.host, options.port)
    self.cookiejar = cookielib.CookieJar()
    
  def send_request(self, url, data = None, headers = None):
    cookie_handler = HTTPCookieProcessor(self.cookiejar)
    redirect_handler = HTTPRedirectHandler()
    opener = build_opener(redirect_handler, cookie_handler)
    req = Request(url=url,  headers=headers if headers else {})
    if data:
      res = opener.open(req, data)
    else:
      res = opener.open(req)
    html = ''.join(res.readlines())
    return html
    
  def get_login_url(self):
    rr = LOGIN_URL % self.url
    rr += urllib.quote_plus(self.url)
    return rr
    
  def get_queue_url(self, queue = None):
    rr = TASKS_URL % self.url
    if queue:
      rr += '?queue=' + queue
    return rr
  
  def login(self):
    url = self.get_login_url()
    self.send_request(url=url, headers={'REFERER': LOGIN_URL % ''})
    #print self.cookiejar

  def run(self, args): 
    queue = args[0] if args else 'default'
    failed_tasks = set()
    self.login()

    while True:   
      url = self.get_queue_url(queue)
      html = self.send_request(url)
      soup = BeautifulSoup(html)
      tasks = []
      for t in soup.findAll(id=re.compile("^runform")):
        task = self.parse(t)
        if task['name'] in failed_tasks:
          continue
        tasks.append(task)
      if not tasks:
        if len(failed_tasks) != 0:
          print 'There are',len(failed_tasks),'failed tasks in',queue
        else:
          print 'There are no tasks in queue: "%s"' % queue
        return
    
      for task in tasks:
        if self.options.list_only:
          print task['name']
          continue
        try:
          url = '%s%s' % (self.url, task['action'])
          print url
          payload = task['payload'] if task['payload'] else ''
          response = self.send_request(url, 
                                       headers = task['headers'],
                                       data = task['payload'])
          soup = BeautifulSoup(self.delete_task(task,queue))
        except Exception,e:
          print e
          failed_tasks.add(task['name'])
      if self.options.list_only:
        break
      
  def delete_task(self, task,queue):
    import urllib
    print 'deleting %s' % task['name']
    
    return self.send_request(
        url=self.get_queue_url(''),
        headers={},
        data = urllib.urlencode([('queue',queue),
                               ('task',task['headers']['X-AppEngine-TaskName']),
                               ('action:deletetask','true')]))
  
  def parse(self, form):
    res = {}
    HEADER_KEY = 'header:'
    res['action'] = form['action']
    res['method'] = form['method']
    res['headers'] = {}
    for e in form:
      if isinstance(e,NavigableString) or e.name != 'input':      
        continue
      attrs = dict(e.attrs)
      if attrs.get('type','') != 'hidden':
        continue
      
      key = attrs['name']
      value = attrs['value']
      if key.startswith(HEADER_KEY):
        res['headers'][key[len(HEADER_KEY):]] = value
      
      elif key == 'payload':
        res['payload'] = value
    res['name'] = res['headers']['X-AppEngine-TaskName']
    return res  
  
def parseargs():
    newargs = []
    from optparse import OptionParser
    parser = OptionParser(usage='%prog [OPTIONS] [queue-name]', 
                          epilog="")
    # pytest options
    df = 'default'
    parser.add_option('-n', '--name', dest='name', default=df,
                      help="name of the queue. default: %s" % df)
    df = os.environ.get('NS_HOSTNAME', 'localhost')
    parser.add_option('-s', '--srv', dest='host', 
                      default=df,
                      help="the host where the server runs. default: %s" % df)
    df = os.environ.get('PCKIDSIS_PORT', 8080)
    parser.add_option('-p', '--port', dest='port', 
                      default=df,
                      help="the port where the server listens. default: %s" % df)
    parser.add_option('-l', '--list', dest='list_only', action="store_true", 
                      default=False,
                      help="Just list the first 25 tasks in the queue and exit")

    # parse the command line
    options, args = parser.parse_args()
    newargs += args
    return options, newargs 
        
options,args = parseargs()
app = CApp(options)    
app.run(args)