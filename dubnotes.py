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
     
    def reauthenticate_user (self, uid, request_token):
        self.set_request_token(request_token)
        self.get_user_and_access_token(uid)
        self.dropbox_client = client.DropboxClient(self.config['server'], self.config['content_server'],
                                                   self.config['port'], self.dropbox_auth, self.access_token)
    
    def set_request_token(self, request_token):
        self.request_token = request_token    
    
    def get_user_and_access_token(self, uid):
        self.user = db_get_user(uid)
        if self.user:
            self.get_access_token()
        else:
            self.obtain_access_token()
            self.user = self.create_user(uid)
      
    def get_access_token(self):
        self.access_token = oauth.OAuthToken(str(self.user.access_key), str(self.user.access_secret))

    def obtain_access_token(self):
        oauth_token = oauth.OAuthToken(str(self.request_token.req_key), str(self.request_token.req_secret))
        self.access_token = self.dropbox_auth.obtain_access_token (oauth_token, self.config['verifier'])
    
    def create_user(self, uid):
        return db_store_user(uid, self.access_token.key, self.access_token.secret)
      
    def obtain_request_token(self):
        return self.dropbox_auth.obtain_request_token()
        
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
          self.auth.dropbox_client.file_delete(self.auth.config['root'], self.request.get('fname'))
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
            f = self.auth.dropbox_client.put_file (self.auth.config['root'], folder, s)
            #self.response.out.write(f.status)
            if f.status != 200:
              pass
              # handle error
              
        # has the file be renamed?
        if fname != '' and os.path.basename(fname) != showname:
          folder, name = os.path.split(fname)
          f = self.auth.dropbox_client.file_move (self.auth.config['root'], fname, os.path.join(folder, showname))
          if f.status != 200:
            pass
            # could not rename
        self.list_view()
              
    def authenticate_user(self):
        #try:
            self.auth = Authenticator()
            if self.is_valid_uid_in_request() and self.is_valid_request_token_in_request():
                self.authenticate_known_user()
            else:
                self.redirect_unknown_user()
        #except:
        #    raise AuthenticationException("Authentication error.")

    def authenticate_known_user(self):
        uid = self.get_uid_from_request()
        request_token = self.get_request_token_from_request()
        self.auth.reauthenticate_user(uid, db_get_token(request_token))
        
    def redirect_unknown_user(self):
        token = self.auth.obtain_request_token()
        db_store_token(token)
        self.redirect_to_dropbox(token, self.auth.dropbox_auth)

    def is_valid_uid_in_request(self):
        if self.get_uid_from_request() == "":
            return False
        return True
        
    def is_valid_request_token_in_request(self):
        if self.get_request_token_from_request() == "":
            return False
        return True
        
    def get_uid_from_request(self):
        uid = self.request.get('uid') 
        return uid

    def get_request_token_from_request(self):
        oauth_token = self.request.get('oauth_token') 
        return oauth_token

    def redirect_to_dropbox(self, token, dropbox_auth):    
        authorize_url = dropbox_auth.build_authorize_url(token, self.request.uri)
        self.redirect(authorize_url)

    def display_authentication_error(self, exception):
        self.response.out.write (exception)

    def create_new_file(self):
      # first check if we have a folder called "notes" under root, if not create it first
      ret = self.auth.dropbox_client.metadata (self.auth.config['root'], self.auth.config['dubnotes_folder'])
      if ret.status == 403:
        self.auth.dropbox_client.create_folder (self.auth.config['root'], self.auth.config['dubnotes_folder'])      
      s = StringIO.StringIO('')
      s.name = 'note_' + datetime.time(datetime.now()).isoformat().split('.')[0].replace(':', '_') + '.txt'
      f = self.auth.dropbox_client.put_file (self.auth.config['root'], self.auth.config['dubnotes_folder'], s)
      self.list_view()
        
    def show_editor(self):
        fname = self.request.get("get")
        content = ''
        if fname != '':
             f = self.auth.dropbox_client.get_file (self.auth.config['root'], fname)
             content = f.read()
             f.close()
        template_values = {'delete_url':' /?uid=' + self.auth.user.uid + '&oauth_token=' + self.auth.request_token.req_key + '&fname=' + fname + '&action=delete',
                         'url':'/?uid=' + self.auth.user.uid + '&oauth_token=' + self.auth.request_token.req_key,
                         'content': content,
                         'fname': fname,
                         'showname': os.path.basename(fname)}
        path = os.path.join(os.path.dirname(__file__), 'editpage.html')
        self.response.out.write(template.render(path, template_values))
        
        
    def list_view(self):
        # Build list of files and folders
        resp = self.auth.dropbox_client.metadata(self.auth.config['root'], self.auth.config['dubnotes_folder'])
        
        if resp.status == 404:
          self.create_new_file()
          
        template_values = {
            'files': [['/?uid=' + self.auth.user.uid + '&oauth_token=' + self.auth.request_token.req_key + '&action=edit&get=' + cgi.escape(x["path"]), os.path.basename(x["path"])] for x in resp.data['contents'] if not x['is_dir']],
            'new_url': '/?uid=' + self.auth.user.uid + '&oauth_token=' + self.auth.request_token.req_key + '&action=new',
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
