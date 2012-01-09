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

def authenticate(reqhandler, config, dba):
    # Get an authenticator for the app 
    # Get the request token
    req_token = dba.obtain_request_token()
    # store token for later
    token = DropToken (key_name=req_token.key)
    token.req_key = req_token.key
    token.req_secret = req_token.secret
    token.datetime = datetime.now()
    token.put()
    
    authorize_url = dba.build_authorize_url(req_token, reqhandler.request.uri)
    #send to authenticator webpapge,  may he return...
    reqhandler.redirect(authorize_url)
  
class AuthenticationException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)
 
class MainPage(webapp.RequestHandler):
    def quick_auth(self):
      # check if we have a uid in the request
      uid = self.request.get('uid')
      self.config = auth.Authenticator.load_config ("dubnotes.ini")
      dba = auth.Authenticator(self.config)
      self.db_client = None
      if uid == "":
        authenticate(self, self.config, dba)
        return
      else:
        # check if we have that token
        req_token = self.request.get('oauth_token')  
        self.token = DropToken.get_by_key_name (req_token)
        if self.token:
          # we have that token, now we learned the uid for that request
          # do we have a access token for that user?
          self.user = User.get_by_key_name (uid)
          if self.user:
            access_token = oauth.OAuthToken(str(self.user.access_key), str(self.user.access_secret))
          else:
            # create a new user entry and try to get an access token
            req_token = oauth.OAuthToken(str(self.token.req_key), str(self.token.req_secret))
            access_token = dba.obtain_access_token (req_token, self.config['verifier'])
            self.user = User (key_name=uid)
            self.user.uid = uid
            self.user.access_key = access_token.key
            self.user.access_secret = access_token.secret
            self.user.put()
          self.db_client = client.DropboxClient(self.config['server'], self.config['content_server'],
                                           self.config['port'], dba, access_token)
      #return self.config, self.db_client, self.token, self.user            
  
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
          self.db_client.file_delete(self.config['root'], self.request.get('fname'))
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
            f = self.db_client.put_file (self.config['root'], folder, s)
            #self.response.out.write(f.status)
            if f.status != 200:
              pass
              # handle error
              
        # has the file be renamed?
        if fname != '' and os.path.basename(fname) != showname:
          folder, name = os.path.split(fname)
          f = self.db_client.file_move (self.config['root'], fname, os.path.join(folder, showname))
          if f.status != 200:
            pass
            # could not rename
        self.list_view()
              
    def authenticate_user(self):
        try:
          self.auth_data = self.quick_auth()
        except:
          raise AuthenticationException("Authentication error.")

    def display_authentication_error(self, exception):
        self.response.out.write (exception)

    def create_new_file(self):
      # first check if we have a folder called "notes" under root, if not create it first
      ret = self.db_client.metadata (self.config['root'], self.config['dubnotes_folder'])
      if ret.status == 403:
        self.db_client.create_folder (self.config['root'], self.config['dubnotes_folder'])      
      s = StringIO.StringIO('')
      s.name = 'note_' + datetime.time(datetime.now()).isoformat().split('.')[0].replace(':', '_') + '.txt'
      f = self.db_client.put_file (self.config['root'], self.config['dubnotes_folder'], s)
      self.list_view()
        
    def show_editor(self):
        fname = self.request.get("get")
        content = ''
        if fname != '':
             f = self.db_client.get_file (self.config['root'], fname)
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
        resp = self.db_client.metadata(self.config['root'], self.config['dubnotes_folder'])
        
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

