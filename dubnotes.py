#vim: set tabstop=4:
#vim: set expandtab:
#vim: set shiftwidth=4:

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')
from dropbox import client, rest, auth
from oauth import oauth
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.webapp import template
import StringIO
import os.path
import cgi
from datetime import datetime

class DropToken(db.Model):
    req_key=db.StringProperty()
    req_secret=db.StringProperty()
    datetime=db.DateTimeProperty()

class User(db.Model):
    uid=db.StringProperty()
    access_key=db.StringProperty()
    access_secret=db.StringProperty()

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
  
 
class MainPage(webapp.RequestHandler):
    def quick_auth(self):
      # check if we have a uid in the request
      uid = self.request.get('uid')
      config = auth.Authenticator.load_config ("dubnotes.ini")
      dba = auth.Authenticator(config)
      db_client = None
      if uid == "":
        authenticate(self, config, dba)
        return
      else:
        # check if we have that token
        req_token = self.request.get('oauth_token')  
        token = DropToken.get_by_key_name (req_token)
        if token:
          # we have that token, now we learned the uid for that request
          # do we have a access token for that user?
          user = User.get_by_key_name (uid)
          if user:
            access_token = oauth.OAuthToken(str(user.access_key), str(user.access_secret))
          else:
            # create a new user entry and try to get an access token
            req_token = oauth.OAuthToken(str(token.req_key), str(token.req_secret))
            access_token = dba.obtain_access_token (req_token, config['verifier'])
            user = User (key_name=uid)
            user.uid = uid
            user.access_key = access_token.key
            user.access_secret=access_token.secret
            user.put()
          db_client = client.DropboxClient(config['server'], config['content_server'], 
                                           config['port'], dba, access_token)
      return config, db_client, token, user            
  
    def post(self):
        try:
          config, db_client, token, user = self.quick_auth()
        except:
          self.response.out.write('Authentication error.')
          return
       
        # save text
        fname = self.request.get("f_name")
        showname = self.request.get("f_showname")
        content = self.request.get("f_content")
        s=StringIO.StringIO(content.encode("utf-8"))
        if fname != '':
            folder, s.name = os.path.split(fname)
            f = db_client.put_file (config['root'], folder, s)
            #self.response.out.write(f.status)
            if f.status != 200:
              pass
              # handle error
              
        # has the file be renamed?
        if fname != '' and os.path.basename(fname) != showname:
          folder, name = os.path.split(fname)
          f = db_client.file_move (config['root'], fname, os.path.join(folder, showname))
          if f.status != 200:
            pass
            # could not rename
        self.list_view(config, db_client, token, user)
              
    def get(self):
        try:
          config, db_client, token, user = self.quick_auth()
        except:
          self.response.out.write('Authentication error.')
          return
       
        # evaluate action
        action = self.request.get('action')
        if action=='edit':
          self.show_editor(config, db_client, token, user)
        elif action=='new':
          self.create_new_file(config, db_client, token, user)
        elif action=='delete':
          db_client.file_delete(config['root'], self.request.get('fname'))
          self.list_view(config, db_client, token, user)
        else:
          self.list_view(config, db_client, token, user)
    
    def create_new_file(self, config, db_client, token, user):
      # first check if we have a folder called "notes" under root, if not create it first
      ret = db_client.metadata (config['root'], config['dubnotes_folder'])
      if ret.status == 403:
        db_client.create_folder (config['root'], config['dubnotes_folder'])      
      s=StringIO.StringIO('')
      s.name='note_' + datetime.time(datetime.now()).isoformat().split('.')[0].replace(':','_') + '.txt'
      f = db_client.put_file (config['root'], config['dubnotes_folder'], s)
      self.list_view(config, db_client, token, user)
        
    def show_editor(self, config, db_client, token, user):
        fname = self.request.get("get")
        content=''
        if fname != '':
             f = db_client.get_file (config['root'], fname)
             content=f.read()
             f.close()
        template_values={'delete_url':' /?uid=' + user.uid + '&oauth_token='+ token.req_key + '&fname=' +fname+ '&action=delete',
                         'url':'/?uid=' + user.uid + '&oauth_token='+ token.req_key, 
                         'content': content, 
                         'fname': fname,
                         'showname': os.path.basename(fname)}
        path = os.path.join(os.path.dirname(__file__), 'editpage.html')
        self.response.out.write(template.render(path, template_values))
        
        
    def list_view(self, config, db_client, token, user):
        # Build list of files and folders
        resp=db_client.metadata(config['root'], config['dubnotes_folder'])
        
        if resp.status == 404:
          self.create_new_file(config, db_client, token, user)
          
        template_values = {
            'files': [['/?uid=' + user.uid + '&oauth_token=' + token.req_key + '&action=edit&get=' + cgi.escape(x["path"]), os.path.basename(x["path"])] for x in resp.data['contents'] if not x['is_dir']],
            'new_url': '/?uid=' + user.uid + '&oauth_token=' + token.req_key + '&action=new',
        }
     
        path = os.path.join(os.path.dirname(__file__), 'mainpage.html')
        self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication(
                                     [('/', MainPage),],
                                     debug=False)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
