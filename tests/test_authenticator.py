import unittest
import sys, os
sys.path.append("..")
os.environ['DUBNOTES_DEBUG'] = "true"
import authentication
from helper import *
from oauth import oauth

class TestSessionFactory(unittest.TestCase):
    def testGetRedirectedSession(self):
        request = {}
        session = authentication.SessionFactory.create(request)
        self.assertEqual (True, isinstance(session, authentication.RedirectedSession)) 
    
    def testGetAuthenticatedSession(self):
        request = DictWithURI([('oauth_token', 'oauth_token'), ('uid', '')])
        session = authentication.SessionFactory.create(request)
        self.assertEqual (True, isinstance(session, authentication.AuthenticatedSession)) 
    
class TestRedirectedSession(unittest.TestCase):
    def setUp(self):
        request = DictWithURI([('uri', 'localhost')])
        self.session = authentication.SessionFactory.create(request)
    
    def testShouldRedirect(self):
        self.assertEqual (True, self.session.needs_redirect())
    
    def testGetURL(self):
        self.assertEqual ("http://localhost:8080/?uid=user&oauth_token=a_request_token", 
                          self.session.get_authorization_url())
    
class TestAuthenticatedSession(unittest.TestCase):
    def setUp(self):
        request = DictWithURI([('oauth_token', 'oauth_token'), ('uid', 'user'), ('uri', 'localhost')])
        self.session = authentication.SessionFactory.create(request)
        
    def testShouldNotRedirect(self):
        self.assertEqual (False, self.session.needs_redirect())
        
    def testAuthenticatorUser(self):
        self.session.authenticate_user()
        self.assertEqual (True, isinstance(self.session.access_token, oauth.OAuthToken))
                          