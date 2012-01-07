from ConfigParser import SafeConfigParser
from oauth import oauth

class Authenticator(object):
    def __init__(self, config):
        pass
    
    @classmethod
    def load_config(self, filename):
        """
        Loads a configuration .ini file, and then pulls out the 'auth' key
        to make a dict you can pass to Authenticator().
        """
        config = SafeConfigParser()
        config_file = open(filename, "r")
        config.readfp(config_file)
        return dict(config.items('auth'))

    def build_authorize_url(self, req_token, callback=None):
        return "http://localhost:8080/?uid=user&oauth_token=a_request_token" 
        
    def obtain_request_token(self):
        return oauth.OAuthToken('a_request_token', 'a_request_secret')

    def obtain_access_token(self, token, verifier):
        return oauth.OAuthToken('an_access_token', 'an_access_secret')

    def obtain_trusted_access_token(self, user_name, user_password):
        return oauth.OAuthToken('a_trusted_access_token', 'a_trusted_access_secret')

