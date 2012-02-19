import unittest
import dubnotes
import sys
sys.path.append("..")

class MinimalRequest():
    def __init__(self, dict):
        self.data = dict
    def get(self, name, default_value=""):
        if not self.data.has_key(name):
            return default_value
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
