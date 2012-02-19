import os
if os.environ.has_key('DUBNOTES_DEBUG'):
    from fake_db import db
else:
    from google.appengine.ext import db
from datetime import datetime

class DropToken(db.Model):
    req_key = db.StringProperty()
    req_secret = db.StringProperty()
    datetime = db.DateTimeProperty()

class User(db.Model):
    uid = db.StringProperty()
    access_key = db.StringProperty()
    access_secret = db.StringProperty()

def db_get_token(token):
    return DropToken.get_by_key_name (token)

def db_store_token(token):
    t = DropToken (key_name=token.key)
    t.req_key = token.key
    t.req_secret = token.secret
    t.datetime = datetime.now()
    t.put()
    return t

def db_get_user (uid):
    return User.get_by_key_name (uid)
        
def db_store_user (uid, key, secret):
    u = User(key_name=uid)
    u.uid = uid
    u.access_key = key
    u.access_secret = secret
    u.put()    
    return u
