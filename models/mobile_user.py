from google.appengine.ext import db

class MobileUser(db.Model):
    '''
    Used in workaround for null user id (helper/push_helper.py)
    We can restructure this once regular oauth logins happen (https://github.com/the-blue-alliance/the-blue-alliance/issues/1069)
    This is not a good long term solution, I don't think
    '''
    user = db.UserProperty(required=True)
