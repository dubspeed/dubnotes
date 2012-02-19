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
   
class MainPage(webapp.RequestHandler):
    def get(self):
        self.evaluate()
        
    def post(self):
        self.evaluate()
    
    def evaluate(self):
        if self.force_authentication() == True:
            self.evaluate_action()

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

    def evaluate_action(self):
        act = action.ActionFactory.create(self.request.get('action'), self.request, self.session)
        path, template_values = act.do()
        self.response.out.write(template.render(path, template_values))
   
    def display_authentication_error(self, exception):
        self.response.out.write (exception)

         
application = webapp.WSGIApplication(
                                     [('/', MainPage), ],
                                     debug=False)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
