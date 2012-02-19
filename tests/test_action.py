import unittest
import sys, os
sys.path.append("..")
os.environ['DUBNOTES_DEBUG'] = "true"
from action import *
import authentication
from helper import *
import fake_dropbox


class TestActions(unittest.TestCase):
    def setUp(self):
        self.request = DictWithURI([('oauth_token', 'oauth_token'), ('uid', 'user')])
        self.session = authentication.SessionFactory.create(self.request)
        self.session.authenticate_user()
        conf = self.session.config
        self.dropbox_client = fake_dropbox.client.DropboxClient(conf['server'], conf['content_server'],
                                                                conf['port'], self.session.dropbox_auth, self.session.access_token)
        
    def testActionFactory(self):
        self.assertEqual (True, isinstance(ActionFactory.create('edit', self.request, self.dropbox_client, self.session), EditAction))
        self.assertEqual (True, isinstance(ActionFactory.create('new',self.request, self.dropbox_client, self.session), NewAction))
        self.assertEqual (True, isinstance(ActionFactory.create('delete',self.request, self.dropbox_client, self.session), DeleteAction))
        self.assertEqual (True, isinstance(ActionFactory.create('save',self.request, self.dropbox_client, self.session), SaveAction))
        self.assertEqual (True, isinstance(ActionFactory.create('list',self.request, self.dropbox_client, self.session), ListAction))
    
    def testEditAction(self):
        request = DictWithURI([('oauth_token', 'oauth_token'), ('uid', 'user'), ('get', 'filename')])
        edit_act = ActionFactory.create('edit', request, self.dropbox_client, self.session)
        path, template = edit_act.do()
        self.assertEqual("../editpage.html", path)
        self.assertEqual("filename", template["fname"])
        
    def testListAction(self):
        list_act = ActionFactory.create('list', self.request, self.dropbox_client, self.session)
        path, template = list_act.do()
        self.assertEqual("../mainpage.html", path)
        self.assertEqual(True, template.has_key("new_url"))
        
        
        