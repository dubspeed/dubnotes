import os, os.path
import cgi
import StringIO
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')
from fake_dropbox import client, rest, auth
from fake_db import db
#from google.appengine.ext import db
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
  
class Session(object):
    def __init__ (self, request):
        self.config = auth.Authenticator.load_config ("dubnotes.ini")
        self.dropbox_auth = auth.Authenticator(self.config)
        self.request = request
  
    def needs_redirect(self):
        return False
  
class RedirectedSession(Session):
    def __init__(self, request):
       super(RedirectedSession, self).__init__(request)
       self.request_token = None
       
    def get_authorization_url(self):
        self.request_token = self.obtain_request_token()
        db_store_token(self.request_token)
        authorize_url = self.dropbox_auth.build_authorize_url(self.request_token, self.request.uri)
        return authorize_url

    def obtain_request_token(self):
        return self.dropbox_auth.obtain_request_token()

    def needs_redirect(self):
        return True


class AuthenticatedSession(Session):
    def __init__(self, request):
        super(AuthenticatedSession, self).__init__(request)
        self.uid = self.request.get('uid')
        self.request_token = db_get_token(self.request.get('oauth_token'))
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
    def create(request):
        if request.get('uid',None) == None or request.get('oauth_token',None) == None:
            return RedirectedSession(request)
        else:
            return AuthenticatedSession(request)

  
class AuthenticationException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

class RedirectionException(AuthenticationException):
    pass
        
class MainPage(webapp.RequestHandler):
    def get(self):
        self.evaluate("get")
        
    def post(self):
        self.evaluate("post")
    
    def evaluate(self, method):
        if self.force_authentication() == True:
            self.get_dropbox_client()
            if method == "get":
                self.evaluate_get_request()
            else:
                self.evaluate_post_request()
                
    def force_authentication(self):
        try:
            self.authenticate_user()
            return True
        except AuthenticationException, e:
            self.display_authentication_error(e)
        except RedirectionException, e:
            return False
        return False

    def authenticate_user(self):
        self.auth = SessionFactory.create(self.request)
        if self.auth.needs_redirect():
            self.redirect(self.auth.get_authorization_url())
            raise RedirectionException ("User redirected")
        self.auth.authenticate_user()

    def get_dropbox_client(self):
        conf = self.auth.config
        self.dropbox_client = client.DropboxClient(conf['server'], conf['content_server'],
                                                   conf['port'], self.auth.dropbox_auth, self.auth.access_token)
        

    # Idee : Strategy Pattern !! -> OCP, jede Action eine Klasse
    def evaluate_get_request(self):
        action = self.request.get('action')
        if action == 'edit':
            self.show_editor()
        elif action == 'new':
            self.create_new_file()
        elif action == 'delete':
            self.dropbox_client.file_delete(self.auth.config['root'], self.request.get('fname'))
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
            f = self.dropbox_client.put_file (self.auth.config['root'], folder, s)
            #self.response.out.write(f.status)
            if f.status != 200:
              pass
              # handle error
              
        # has the file be renamed?
        if fname != '' and os.path.basename(fname) != showname:
          folder, name = os.path.split(fname)
          f = self.dropbox_client.file_move (self.auth.config['root'], fname, os.path.join(folder, showname))
          if f.status != 200:
            pass
            # could not rename
        self.list_view()
           
              
    def display_authentication_error(self, exception):
        self.response.out.write (exception)

    def create_new_file(self):
      # first check if we have a folder called "notes" under root, if not create it first
      ret = self.dropbox_client.metadata (self.auth.config['root'], self.auth.config['dubnotes_folder'])
      if ret.status == 403:
        self.dropbox_client.create_folder (self.auth.config['root'], self.auth.config['dubnotes_folder'])      
      s = StringIO.StringIO('')
      s.name = 'note_' + datetime.time(datetime.now()).isoformat().split('.')[0].replace(':', '_') + '.txt'
      f = self.dropbox_client.put_file (self.auth.config['root'], self.auth.config['dubnotes_folder'], s)
      self.list_view()
        
    def show_editor(self):
        fname = self.request.get("get")
        content = ''
        if fname != '':
             f = self.dropbox_client.get_file (self.auth.config['root'], fname)
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
        resp = self.dropbox_client.metadata(self.auth.config['root'], self.auth.config['dubnotes_folder'])
        
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
