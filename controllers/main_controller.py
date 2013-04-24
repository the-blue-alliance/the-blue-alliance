import os
import logging
import datetime
import time
import secrets
import json
import sys

from google.appengine.api import memcache
from google.appengine.ext import ndb, webapp
sys.modules['ndb'] = ndb
from google.appengine.ext.webapp import template

import tba_config

from base_controller import BaseHandler, CacheableHandler
from simpleauth import SimpleAuthHandler
from helpers.event_helper import EventHelper
from webapp2_extras import auth, sessions

from models.event import Event
from models.team import Team
from models.sitevar import Sitevar

def render_static(page):
    memcache_key = "main_%s" % page
    html = memcache.get(memcache_key)
    
    if html is None:
        path = os.path.join(os.path.dirname(__file__), "../templates/%s.html" % page)
        html = template.render(path, {})
        if tba_config.CONFIG["memcache"]: memcache.set(memcache_key, html, 86400)
    
    return html
            
class MainKickoffHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_kickoff"
        self._cache_version = 3

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/index_kickoff.html")
        return template.render(path, {})
                  
class MainBuildseasonHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_buildseason"
        self._cache_version = 1

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/index_buildseason.html")
        return template.render(path, {})

class MainCompetitionseasonHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60
        self._cache_key = "main_competitionseason"
        self._cache_version = 5

    def _render(self, *args, **kw):
        week_events = EventHelper.getWeekEvents()
        template_values = {
            "events": week_events,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/index_competitionseason.html')
        return template.render(path, template_values)

class ContactHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_contact"
        self._cache_version = 1

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/contact.html")
        return template.render(path, {})

class HashtagsHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_hashtags"
        self._cache_version = 1

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/hashtags.html")
        return template.render(path, {})
        
class AboutHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_about"
        self._cache_version = 1

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/about.html")
        return template.render(path, {})

class ThanksHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_thanks"
        self._cache_version = 1

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/thanks.html")
        return template.render(path, {})

class OprHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_opr"
        self._cache_version = 1

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/opr.html")
        return template.render(path, {})

class SearchHandler(BaseHandler):
    def get(self):
        try:
            q = self.request.get("q")
            logging.info("search query: %s" % q)
            if q.isdigit():
                team_id = "frc%s" % q
                team = Team.get_by_id(team_id)
                if team:
                    self.redirect(team.details_url)
                    return None
        except Exception, e:
            logging.warning("warning: %s" % e)
        finally:
            self.response.out.write(render_static("search"))

class GamedayHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_gameday"
        self._cache_version = 1

    def _render(self, *args, **kw):
        special_webcasts_future = Sitevar.get_by_id_async('gameday.special_webcasts')
        special_webcasts_temp = special_webcasts_future.get_result()
        if special_webcasts_temp:
            special_webcasts_temp = special_webcasts_temp.contents
        else:
            special_webcasts_temp = {}
        special_webcasts =  []
        for webcast in special_webcasts_temp.values():
            toAppend = {}
            for key, value in webcast.items():
                toAppend[str(key)] = str(value)
            special_webcasts.append(toAppend)

        ongoing_events = []
        ongoing_events_w_webcasts = []
        week_events = EventHelper.getWeekEvents()
        for event in week_events:
            if event.within_a_day:
                ongoing_events.append(event)
                if event.webcast:
                    valid = []
                    for webcast in event.webcast:
                        if 'type' in webcast and 'channel' in webcast:
                            event_webcast = {'event': event}
                            valid.append(event_webcast)
                    # Add webcast numbers if more than one for an event
                    if len(valid) > 1:
                        count = 1
                        for event in valid:
                            event['count'] = count
                            count += 1
                    ongoing_events_w_webcasts += valid
        
        template_values = {'special_webcasts': special_webcasts,
                           'ongoing_events': ongoing_events,
                           'ongoing_events_w_webcasts': ongoing_events_w_webcasts}
        
        path = os.path.join(os.path.dirname(__file__), '../templates/gameday.html')
        return template.render(path, template_values)

class ChannelHandler(BaseHandler):
    # This is required for the FB JSSDK
    def get(self):
        expires = 60*60*24*365
        self.response.headers.add_header("Pragma", "public")
        self.response.headers.add_header("Cache-Control", "max-age="+str(expires))
        expires_date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(expires + time.time()))
        self.response.headers.add_header("Expires", expires_date)
        self.response.out.write('<script src="//connect.facebook.net/en_US/all.js"></script>')

class PageNotFoundHandler(BaseHandler):
    def get(self):
        self.error(404)
        self.response.out.write(render_static("404"))

class WebcastsHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_webcasts"
        self._cache_version = 2

    def _render(self, *args, **kw):
        event_keys = Event.query(Event.year == 2013).order(Event.start_date).fetch(500, keys_only=True)
        events = ndb.get_multi(event_keys)

        template_values = {
            'events': events,
        }
        
        path = os.path.join(os.path.dirname(__file__), '../templates/webcasts.html')
        return template.render(path, template_values)

class RecordHandler(CacheableHandler):
    def __init__(self, *args, **kw):
        super(CacheableHandler, self).__init__(*args, **kw)
        self._cache_expiration = 60 * 60 * 24 * 7
        self._cache_key = "main_record"
        self._cache_version = 1

    def _render(self, *args, **kw):
        path = os.path.join(os.path.dirname(__file__), "../templates/record.html")
        return template.render(path, {})

class AccountHandler(BaseHandler):
    def get(self):
        if self.logged_in:
            template_values = {
                'user': self.current_user,
                'session': self.auth.get_user_by_session().items(),
            }
        else:
            template_values = {
                'msg': self.session.get_flashes('msg'),
            }
        path = os.path.join(os.path.dirname(__file__), '../templates/account.html')
        self.response.out.write(template.render(path, template_values))

class AuthHandler(BaseHandler, SimpleAuthHandler):
    """Authentication handler for OAuth 2.0, 1.0(a) and OpenID."""

    # Enable optional OAuth 2.0 CSRF guard
    OAUTH2_CSRF_STATE = True
  
    USER_ATTRS = {
        'facebook' : {
            'id'     : lambda id: ('avatar_url', 
                'http://graph.facebook.com/{0}/picture?type=large'.format(id)),
            'name'   : 'name',
            'link'   : 'link',
            'email'  : 'email'
        },
        'google'   : {
            'picture': 'avatar_url',
            'name'   : 'name',
            'link'   : 'link',
            'email'  : 'email'
        },
        'windows_live': {
            'avatar_url': 'avatar_url',
            'name'      : 'name',
            'link'      : 'link'
        },
        'twitter'  : {
            'profile_image_url': 'avatar_url',
            'screen_name'      : 'name',
            'link'             : 'link'
        },
        'linkedin' : {
            'picture-url'       : 'avatar_url',
            'first-name'        : 'name',
            'public-profile-url': 'link'
        },
        'foursquare'   : {
            'photo'    : lambda photo: ('avatar_url', photo.get('prefix') + '100x100' + photo.get('suffix')),
            'firstName': 'firstName',
            'lastName' : 'lastName',
            'contact'  : lambda contact: ('email',contact.get('email')),
            'id'       : lambda id: ('link', 'http://foursquare.com/user/{0}'.format(id))
        },
        'openid'   : {
            'id'      : lambda id: ('avatar_url', '/img/missing-avatar.png'),
            'nickname': 'name',
            'email'   : 'link'
        }
    }

    def _on_signin(self, data, auth_info, provider):
        """Callback whenever a new or existing user is logging in.
         data is a user info dictionary.
         auth_info contains access token or oauth token and secret.
        """
        auth_whitelist = Sitevar.get_by_id("auth.whitelist")
        if data['id'] in auth_whitelist.values_json:
            auth_id = '%s:%s' % (provider, data['id'])
            logging.info('Looking for a user with id %s', auth_id)
    
            user = self.auth.store.user_model.get_by_auth_id(auth_id)
            _attrs = self._to_user_model_attrs(data, self.USER_ATTRS[provider])

            if user:
                logging.info('Found existing user to log in')
                # Existing users might've changed their profile data so we update our
                # local model anyway. This might result in quite inefficient usage
                # of the Datastore, but we do this anyway for demo purposes.
                #
                # In a real app you could compare _attrs with user's properties fetched
                # from the datastore and update local user in case something's changed.
                user.populate(**_attrs)
                user.put()
                self.auth.set_session(
                self.auth.store.user_to_dict(user))
      
            else:
                # check whether there's a user currently logged in
                # then, create a new user if nobody's signed in, 
                # otherwise add this auth_id to currently logged in user.

                if self.logged_in:
                    logging.info('Updating currently logged in user')
        
                    u = self.current_user
                    u.populate(**_attrs)
                    # The following will also do u.put(). Though, in a real app
                    # you might want to check the result, which is
                    # (boolean, info) tuple where boolean == True indicates success
                    # See webapp2_extras.appengine.auth.models.User for details.
                    u.add_auth_id(auth_id)
        
                else:
                    logging.info('Creating a brand new user')
                    ok, user = self.auth.store.user_model.create_user(auth_id, **_attrs)
                    if ok:
                        self.auth.set_session(self.auth.store.user_to_dict(user))

            # Go to the profile page
            self.redirect('/account')
        else:
            self.session.add_flash('Error: Unauthorized user ID', key='msg')
            self.redirect('/account')

    def logout(self):
        self.auth.unset_session()
        self.redirect('/')

    def handle_exception(self, exception, debug):
        logging.error(exception)
        self.session.add_flash('Error. Please try again later.', key='msg')
        self.redirect('/account')

    def _callback_uri_for(self, provider):
        return self.uri_for('auth_callback', provider=provider, _full=True)
    
    def _get_consumer_info_for(self, provider):
        """Returns a tuple (key, secret) for auth init requests."""
        return secrets.AUTH_CONFIG[provider]
    
    def _to_user_model_attrs(self, data, attrs_map):
        """Get the needed information from the provider dataset."""
        user_attrs = {}
        for k, v in attrs_map.iteritems():
            attr = (v, data.get(k)) if isinstance(v, str) else v(data.get(k))
            user_attrs.setdefault(*attr)

        return user_attrs
