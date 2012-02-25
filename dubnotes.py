import os, os.path
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')
if os.environ.has_key('DUBNOTES_DEBUG'):
    from fake_dropbox import client, rest, auth
else:
    from dropbox import client, rest, auth
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from google.appengine.ext.webapp import template
import authentication
import database
import action 
   
class PageTemplate(webapp.RequestHandler):
    def get(self):
        self.notename = ""
        self.evaluate()

    def post(self):
        self.notename = ""
        self.evaluate()
    
    def evaluate(self):
        if self.force_authentication() == True:
            self.evaluate_action(self.action)

    def force_authentication(self):
        try:
            self.authenticate_user()
            return True
        except authentication.AuthenticationException, e:
            self.display_authentication_error(e)
        except authentication.RedirectionException, e:
            return False
        return False

    def authenticate_user(self):
        self.session = authentication.SessionFactory.create(self.request)
        if self.session.needs_redirect():
            self.redirect(self.session.get_authorization_url())
            raise authentication.RedirectionException ("User redirected")
        self.session.authenticate_user()

    def evaluate_action(self, page_action):
        act = action.ActionFactory.create(page_action, self.notename, self.request, self.session)
        path, template_values = act.do()
        self.response.out.write(template.render(path, template_values))
   
    def display_authentication_error(self, exception):
        self.response.out.write (exception)

class ListPage(PageTemplate):
    def __init__(self):
        super(ListPage, self).__init__()
        self.action = "list"
           
    def post(self):
        self.action = "save"
        super(ListPage, self).post()

class EditPage(PageTemplate):
    def __init__(self):
        super(EditPage, self).__init__()
        self.action = "edit"
    
    def get(self, notename):
        self.notename = notename
        self.evaluate()
    
class DeletePage(PageTemplate):
    def __init__(self):
        super(DeletePage, self).__init__()
        self.action = "delete"
   
    def get(self, notename):
        self.notename = notename
        self.evaluate()

class NewPage(PageTemplate):
    def __init__(self):
        super(NewPage, self).__init__()
        self.action = "new"

class JSONPage(PageTemplate):
    def __init__(self):
         super(JSONPage, self).__init__()
         self.action = "json"

class AuthenticatePage(PageTemplate):
    def __init__(self):
         super(AuthenticatePage, self).__init__()
         self.action = "authenticate"
         self.notename = ""
         
    def get(self):
        uid = self.request.get('uid', None)
        token = self.request.get('oauth_token', None)
        redirect_url = self.request.get('url', None)
        if uid != None and token != None and redirect_url != None:
            self.redirect(redirect_url + "?uid="+uid+"&oauth_token="+token)
        self.evaluate()
         
application = webapp.WSGIApplication([ ('/notes', ListPage), 
                                       (r'/edit/(.*?)', EditPage), 
                                       (r'/delete/(.*?)', DeletePage),
                                       ('/new', NewPage),
                                       ('/json', JSONPage), 
                                       ('/authenticate', AuthenticatePage),], 
                                     debug=False)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
