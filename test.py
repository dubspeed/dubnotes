import os, os.path
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from google.appengine.ext.webapp import template
   
class TestPage(webapp.RequestHandler):
    def get(self, userid):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("huhu get %s" % (userid,))

    def post(self):
        self.response.out.write("huhu post")    
         
application = webapp.WSGIApplication([ (r'/(.*?)/edit', TestPage),
                                     ], 
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
