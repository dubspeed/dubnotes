from datetime import datetime
import unittest

class Model(object):
    @classmethod
    def get_by_key_name(self, key_name):
        if key_name == "user":
            return UserModel(key_name)
        elif key_name == "nonexisting_user":
            return None
        else:
            return TokenModel(key_name)
   
    def __init__(self, key_name):
        pass
    
    def put(self):
        pass
    
class TokenModel(Model):
    def __init__(self, key_name):
        super(TokenModel, self).__init__(key_name)
        self.req_key = "a_request_key"
        self.req_secret = 'a_request_secret'
        self.datetime= datetime(2012, 01, 01, 00, 00,00)

class UserModel(Model):
    def __init__(self, key_name):
        super(UserModel, self).__init__(key_name)
        self.access_key = 'an_access_key'
        self.access_secret = 'an_access_secret'
        self.uid = 'user'
    
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
    def testUnknownUser(self): 
        user_model = Model.get_by_key_name("non_existing_user")
        assert user_model == None
    def testAnyThingIsToken(self):
        token_model = Model.get_by_key_name("fdmskafldsa")
        assert token_model.req_key == "a_request_key"