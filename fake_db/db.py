from datetime import datetime
import unittest

class Model(object):
    @classmethod
    def get_by_key_name(self, key_name):
        if key_name == "nonexisting_user":
            return None
        return Model(key_name)
   
    def __init__(self, key_name):
        #print "--> called with keyname %s" % key_name
        if key_name == "user":
            self.access_key = 'an_access_key'
            self.access_secret = 'an_access_secret'
            self.uid = 'user'
        else:
            self.req_key = "a_request_key"
            self.req_secret = 'a_request_secret'
            self.datetime= datetime(2012, 01, 01, 00, 00,00)
    def put(self):
        pass
    
def StringProperty():
    pass

def DateTimeProperty():
    pass

class ModelTests(unittest.TestCase):
    def testUserModel(self):
        user_model = Model.get_by_key_name("user")
        assert user_model.access_key == "an_access_key"
        assert user_model.access_secret == "an_access_secret"
        assert user_model.uid == "user"
    def testDropToken(self):
        token_model = Model.get_by_key_name("droptoken")
        assert token_model.req_key == "a_request_key"
        assert token_model.req_secret == "a_request_secret"
        assert token_model.datetime == datetime(2012, 01, 01, 00, 00,00)
        