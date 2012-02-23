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
        self.evaluate()

    def post(self):
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
        self.session = authentication.SessionFactory.create(self.request.uri, self.uid, self.oauth_token)
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
        self.notename = ""
    
    def get(self, uid):
        self.uid = uid
        self.oauth_token = self.request.get('oauth_token', None)
        super(ListPage, self).get()
           
    def post(self):
        self.action = "save"
        super(ListPage, self).post()

class EditPage(PageTemplate):
    def __init__(self):
        super(EditPage, self).__init__()
        self.action = "edit"
        self.notename = ""
 
    def get(self, uid, note):
        self.uid = uid
        self.oauth_token = self.request.get('oauth_token', None)
        self.notename = note
        self.evaluate()
 
class RedirectPage(PageTemplate):
    def __init__(self):
        super(RedirectPage, self).__init__()

    def get(self):
        self.uid = self.request.get("uid")
        self.oauth_token = self.request.get('oauth_token')
        self.redirect("http://10.0.1.34:8080/"+self.uid+"/note?oauth_token="+self.oauth_token)
         
application = webapp.WSGIApplication([ (r'/(.*?)/note', ListPage), 
                                       (r'/(.*?)/note/(.*?)', EditPage),
                                       (r'/redirect', RedirectPage) ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
