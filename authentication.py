import os
if os.environ.has_key('DUBNOTES_DEBUG'):
    from fake_dropbox import client, rest, auth
else:
    from dropbox import client, rest, auth
from oauth import oauth
from database import *

class Session(object):
    def __init__ (self):
        dubnotes_path = os.path.join(os.path.dirname(__file__), 'dubnotes.ini') 
        self.config = auth.Authenticator.load_config (dubnotes_path)
        self.dropbox_auth = auth.Authenticator(self.config)
  
    def needs_redirect(self):
        return False
  
class RedirectedSession(Session):
    def __init__(self, uri):
       super(RedirectedSession, self).__init__()
       self.request_token = None
       self.uri = uri
       
    def get_authorization_url(self):
        self.request_token = self.obtain_request_token()
        db_store_token(self.request_token)
        authorize_url = self.dropbox_auth.build_authorize_url(self.request_token, "http://10.0.1.34:8080/redirect")
        return authorize_url

    def obtain_request_token(self):
        return self.dropbox_auth.obtain_request_token()

    def needs_redirect(self):
        return True

class AuthenticatedSession(Session):
    def __init__(self, uid, oauth_token):
        super(AuthenticatedSession, self).__init__()
        self.uid = uid
        self.request_token = db_get_token(oauth_token)
        self.access_token = None
        self.user = None

    def authenticate_user (self):
        self.get_user_and_access_token()
    
    def get_user_and_access_token(self):
        self.user = db_get_user(self.uid)
        if self.user:
            self.get_access_token()
        else:
            self.obtain_access_token()
            self.user = self.create_user()
  
    def get_access_token(self):
        self.access_token = oauth.OAuthToken(str(self.user.access_key), str(self.user.access_secret))

    def obtain_access_token(self):
        oauth_token = oauth.OAuthToken(str(self.request_token.req_key), str(self.request_token.req_secret))
        self.access_token = self.dropbox_auth.obtain_access_token (oauth_token, self.config['verifier'])
    
    def create_user(self):
        return db_store_user(self.uid, self.access_token.key, self.access_token.secret)
 
class SessionFactory:
    @staticmethod 
    def create(uri, uid, oauth_token):
        if oauth_token == None:
            return RedirectedSession(uri)
        else:
            return AuthenticatedSession(uid, oauth_token)

  
class AuthenticationException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

class RedirectionException(AuthenticationException):
    pass