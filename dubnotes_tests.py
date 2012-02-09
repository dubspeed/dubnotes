import unittest
import httplib
import string
import dubnotes
import sys
import fake_dropbox

class PseudoSocket(object):
    def write(self, stuff):
        self.data = stuff
        
class StdOutRedirector:
    def __init__(self):
        self.out = PseudoSocket()
        self.headers = {}
    def set_status(self, status):
        self.status = status
    def clear(self):
        pass

class DictWithURI(dict):
    uri = "" 

class DubnotesOnlineTests(unittest.TestCase):
    def setUp(self):
        self.httpconnection = httplib.HTTPConnection('localhost:8080')
        self.mainpage = dubnotes.MainPage()
        self.mainpage.response = StdOutRedirector()
    
    def _testCorrectHTTPRequest(self):
        response = self.requestPage("/")
        assert isinstance(response, httplib.HTTPResponse), "wrong or missing http-Response"
    
    def _testRedirectToDropboxWhenUnauthenticated(self):
        response = self.requestPage("/")
        #assert response.status == 302, "expect 302 == FOUND"
        assert string.find(response.msg.get("location", ""), "https://www.dropbox.com/0/oauth/authorize") >= 0, "wrong website"
    
    def _testDubnotesLandingPage(self):
        response = self.requestPage("/?uid=3xxxxxxx98&oauth_token=6xxxxxxxxxhic")
        assert response.status == 200, "expect 200 == OKAY"
        assert string.find(response.read(), "Dub Notes") >= 0, "wrong website"
    
    def requestPage(self, url_part):
        self.httpconnection.request("GET", url_part)
        return self.httpconnection.getresponse()
    
class DubnotesOfflineTests(unittest.TestCase):
    def setUp(self):
        self.mainpage = dubnotes.MainPage()
        self.mainpage.response = StdOutRedirector()
    
    def testQuickAuthOnFakeDropbox(self):
        self.mainpage.request = {'oauth_token':'oauth_token', 'uid':'user'}
        self.mainpage.authenticate_user()
        assert self.mainpage.auth.user.uid == 'user'
        
    def testPartitialAuthentication(self):
        self.mainpage.request = DictWithURI([('oauth_token', 'oauth_token')])
        self.mainpage.force_authentication()
        assert isinstance(self.mainpage.auth, dubnotes.RedirectedSession)
        self.assertEqual (False, self.mainpage.force_authentication())
        self.mainpage.request = DictWithURI([('uid', 'user')])
        with self.assertRaises(dubnotes.AuthenticationException):
            self.mainpage.authenticate_user()
        self.assertEqual (False, self.mainpage.force_authentication())
        assert isinstance(self.mainpage.auth, dubnotes.RedirectedSession)
        
    def testQuickAuthWithUnknownUser(self):
        self.mainpage.request = DictWithURI([('uid', '')])
        with self.assertRaises(dubnotes.AuthenticationException):
            self.mainpage.authenticate_user()
            
        assert self.mainpage.response.status == 302
        assert self.mainpage.response.headers['Location'] == 'http://localhost:8080/?uid=user&oauth_token=a_request_token'
      
    def testAuthentictionWithWrongUser(self):
        self.mainpage.request = {'oauth_token':'a_request_token', 'uid':'non_existing_user'}
        self.mainpage.authenticate_user()
        assert self.mainpage.auth.user.uid == 'non_existing_user'

    def testListPage(self):
        request = {
                   'oauth_token':'oauth_token', 
                   'uid':'user',
                   }
        testdata = {'contents': [
                                 {'path': "a_file.txt", 'is_dir':False},
                                 {'path': "another_file.txt", "is_dir":False},
                                 {'path': "a subdir", 'is_dir': True}
                                ], 
                    }
        response = self.makeFakeGetRequest(request, testdata)
        self.assertListView(response)
        
    def testEditPageViaGet(self):
        request = { 
                    'oauth_token':'oauth_token', 
                    'uid':'user',
                    'get':'a_file', 
                    'action': 'edit'
                   }
        testdata = 'This is a testfile'
        response = self.makeFakeGetRequest(request, testdata)
        assert response.find(testdata)
        
    def testFileCreation(self):
        # create_new_file is basically == list_view, so it expects a list as result
        request = { 
                    'oauth_token':'oauth_token', 
                    'uid':'user',
                    'action': 'new'
                   }
        testdata = {'contents': [
                                 {'path': "a_file.txt", 'is_dir':False},
                                 {'path': "another_file.txt", "is_dir":False},
                                 {'path': "a subdir", 'is_dir': True}
                                ], 
                    }
        response = self.makeFakeGetRequest(request, testdata)
        self.assertListView(response)
        
    def testFileCreationException(self):
        # create_new_file tries to create a folder 
        # via db_client.create_folder --> this method
        # does not exists in dropbox (it is called 
        # file_create_folder -> so we test for the exception
        request = { 
                    'oauth_token':'oauth_token', 
                    'uid':'user',
                    'action': 'new'
                   }
        try:
            response = self.makeFakeGetRequest(request, None, 403)
        except AttributeError as e:
            assert True
        else:
            assert False 
        
    def testFileDelete(self):
        # file delete end with a list view
        request = { 
                    'oauth_token':'oauth_token', 
                    'uid':'user',
                    'action': 'delete',
                    'fname': 'a_file'
                   }
        testdata = {'contents': [
                                 {'path': "a_file.txt", 'is_dir':False},
                                 {'path': "another_file.txt", "is_dir":False},
                                 {'path': "a subdir", 'is_dir': True}
                                ], 
                    }
        response = self.makeFakeGetRequest(request, testdata, status=202)
        self.assertListView(response)
        
    def assertListView(self, response):
        assert response.find('<h1>Dub Notes</h1>')
        assert response.find('get=a_file.txt">a_file.txt</a>')
        assert response.find("?uid=user")
        assert response.find("oauth_token=a_request_key")
        
    def makeFakeGetRequest(self, request, testdata=None, status=202):
        self.mainpage.request = request
        self.mainpage.authenticate_user()
        fake_dropbox.client.DropboxClient.set_demo_data(testdata)
        fake_dropbox.client.DropboxClient.set_demo_status(status)
        self.mainpage.get()
        return self.mainpage.response.out.data

class MinimalRequest():
    def __init__(self, dict):
        self.data = dict
    def get(self, name):
        return self.data[name]

class DubnotesPostTests(unittest.TestCase):
    def setUp(self):
        self.mainpage = dubnotes.MainPage()
        self.mainpage.response = StdOutRedirector()
    
    def testPostFile(self):
        request = { 
                    'oauth_token':'oauth_token', 
                    'uid':'user',
                    'f_name': 'a_file',
                    'f_showname': 'a cute file',
                    'f_content': 'ths is a test'
                   }
        self.mainpage.request = MinimalRequest(request)
        self.mainpage.post()
        
if __name__ == "__main__":
    import fake_dropbox
    suites = []
    suites.append(unittest.TestLoader().loadTestsFromTestCase(DubnotesOnlineTests))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(DubnotesOfflineTests))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(DubnotesPostTests))
    suites.append(unittest.TestLoader().loadTestsFromTestCase(fake_dropbox.client.ClientTests))
    suite = unittest.TestSuite(suites)
    unittest.TextTestRunner(verbosity=2).run(suite)