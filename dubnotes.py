import os, os.path
import cgi
import StringIO
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')
from fake_dropbox import client, rest, auth
from fake_db import db
from oauth import oauth
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from google.appengine.ext.webapp import template
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
  
class AuthenticationException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

class Authenticator:
    def __init__ (self):
        self.config = auth.Authenticator.load_config ("dubnotes.ini")
        self.dropbox_auth = auth.Authenticator(self.config)
        self.user = self.token = self.dropbox_client = None

    def obtain_request_token(self):
        return self.dropbox_auth.obtain_request_token()
            
    def reauthenticate_user(self, uid, token):
        if token:
            self.token = token
            self.user = db_get_user(uid)
            if self.user:
              access_token = oauth.OAuthToken(str(self.user.access_key), str(self.user.access_secret))
            else:
              # create a new user entry and try to get an access token
              oauth_token = oauth.OAuthToken(str(token.req_key), str(token.req_secret))
              access_token = self.dropbox_auth.obtain_access_token (oauth_token, self.config['verifier'])
              self.user = db_store_user(uid, access_token.key, access_token.secret)
            
            self.dropbox_client = client.DropboxClient(self.config['server'], self.config['content_server'],
                                             self.config['port'], self.dropbox_auth, access_token)
        else:
            # case not handled ... ?
            pass

class MainPage(webapp.RequestHandler):
    def get(self):
        if self.force_authentication() == True:
            self.evaluate_get_request()

    def post(self):
        if self.force_authentication() == True:
            self.evaluate_post_request()

    def force_authentication(self):
        try:
            self.authenticate_user()
            return True
        except AuthenticationException as e:
            self.display_authentication_error(e)
        return False

    def evaluate_get_request(self):
        action = self.request.get('action')
        if action == 'edit':
          self.show_editor()
        elif action == 'new':
          self.create_new_file()
        elif action == 'delete':
          self.dropbox_client.file_delete(self.config['root'], self.request.get('fname'))
          self.list_view()
        else:
          self.list_view()

    def evaluate_post_request(self):       
        # save text
        fname = self.request.get("f_name")
        showname = self.request.get("f_showname")
        content = self.request.get("f_content")
        s = StringIO.StringIO(content.encode("utf-8"))
        if fname != '':
            folder, s.name = os.path.split(fname)
            f = self.dropbox_client.put_file (self.config['root'], folder, s)
            #self.response.out.write(f.status)
            if f.status != 200:
              pass
              # handle error
              
        # has the file be renamed?
        if fname != '' and os.path.basename(fname) != showname:
          folder, name = os.path.split(fname)
          f = self.dropbox_client.file_move (self.config['root'], fname, os.path.join(folder, showname))
          if f.status != 200:
            pass
            # could not rename
        self.list_view()
              
    def authenticate_user(self):
        self.authenticator = Authenticator()
        try:
            self.decide_authentication_path()
            self.dropbox_client = self.authenticator.dropbox_client
            self.user = self.authenticator.user
            self.config = self.authenticator.config
            self.token = self.authenticator.token
        except:
            raise AuthenticationException("Authentication error.")

    def decide_authentication_path(self):
        if self.is_valid_uid_in_request():
            uid = self.get_uid_from_request()
            oauth_token = self.get_oauth_token_from_request()
            self.authenticator.reauthenticate_user(uid, db_get_token(oauth_token))
        else:
            token = self.authenticator.obtain_request_token()
            db_store_token(token)
            self.redirect_to_dropbox(token, self.authenticator.dropbox_auth)

    def is_valid_uid_in_request(self):
        if self.get_uid_from_request() == "":
            return False
        return True
        
    def get_uid_from_request(self):
        uid = self.request.get('uid') 
        return uid

    def get_oauth_token_from_request(self):
        oauth_token = self.request.get('oauth_token') 
        return oauth_token

    def redirect_to_dropbox(self, token, dropbox_auth):    
        authorize_url = dropbox_auth.build_authorize_url(token, self.request.uri)
        self.redirect(authorize_url)

    def display_authentication_error(self, exception):
        self.response.out.write (exception)

    def create_new_file(self):
      # first check if we have a folder called "notes" under root, if not create it first
      ret = self.dropbox_client.metadata (self.config['root'], self.config['dubnotes_folder'])
      if ret.status == 403:
        self.dropbox_client.create_folder (self.config['root'], self.config['dubnotes_folder'])      
      s = StringIO.StringIO('')
      s.name = 'note_' + datetime.time(datetime.now()).isoformat().split('.')[0].replace(':', '_') + '.txt'
      f = self.dropbox_client.put_file (self.config['root'], self.config['dubnotes_folder'], s)
      self.list_view()
        
    def show_editor(self):
        fname = self.request.get("get")
        content = ''
        if fname != '':
             f = self.dropbox_client.get_file (self.config['root'], fname)
             content = f.read()
             f.close()
        template_values = {'delete_url':' /?uid=' + self.user.uid + '&oauth_token=' + self.token.req_key + '&fname=' + fname + '&action=delete',
                         'url':'/?uid=' + self.user.uid + '&oauth_token=' + self.token.req_key,
                         'content': content,
                         'fname': fname,
                         'showname': os.path.basename(fname)}
        path = os.path.join(os.path.dirname(__file__), 'editpage.html')
        self.response.out.write(template.render(path, template_values))
        
        
    def list_view(self):
        # Build list of files and folders
        resp = self.dropbox_client.metadata(self.config['root'], self.config['dubnotes_folder'])
        
        if resp.status == 404:
          self.create_new_file()
          
        template_values = {
            'files': [['/?uid=' + self.user.uid + '&oauth_token=' + self.token.req_key + '&action=edit&get=' + cgi.escape(x["path"]), os.path.basename(x["path"])] for x in resp.data['contents'] if not x['is_dir']],
            'new_url': '/?uid=' + self.user.uid + '&oauth_token=' + self.token.req_key + '&action=new',
        }
     
        path = os.path.join(os.path.dirname(__file__), 'mainpage.html')
        self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication(
                                     [('/', MainPage), ],
                                     debug=False)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
