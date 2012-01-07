#from fake_dropbox import rest
import httplib
import unittest

class FakeHTTPResponse(httplib.HTTPResponse):
    def __init__(self):
        self.fp=0
    def getheader(self, name, default=None):
        return self._fetch_response.headers.get(name, default)
    def getheaders(self):
        return self._fetch_response.headers.items()
    @property
    def msg(self):
        msg = mimetools.Message(StringIO.StringIO(''))
        for name, value in self._fetch_response.headers.items():
            msg[name] = str(value)
        return msg
    version = 11
    def status(self):
        return self.status
    def set_status(self, status):
        self.status = status
    @property
    def reason(self):
        return 202
    def read(self):
        return self.data
    def set_data(self, data):
        self.data=data

class DropboxClient(object):
    data = None     # shared state
    status = 0
    
    def __init__(self, api_host, content_host, port, auth, token):      
        pass
    
    @classmethod
    def set_demo_data (self, data):
        DropboxClient.data = data

    @classmethod
    def set_demo_status (self, status):
        DropboxClient.status = status

#   def request(self, host, method, target, params, callback):
#        return url, headers, params

#    def account_info(self, status_in_response=False, callback=None):
#        return rest.RESTResponse(FakeHTTPResponse())

    def fake_http_response(self):
        fakeresp=FakeHTTPResponse()
        fakeresp.set_status(DropboxClient.status)
        fakeresp.set_data(DropboxClient.data)
        return fakeresp
    
    def put_file(self, root, to_path, file_obj):
        return self.fake_http_response()
        
    def get_file(self, root, from_path):
        return self.fake_http_response()
        
    def file_delete(self, root, path, callback=None):
        return self.fake_http_response()

    ## files and folder
    def metadata(self, root, path, file_limit=10000, hash=None, list=True, status_in_response=False, callback=None):
        return self.fake_http_response()

    def file_create_folder(self, root, path, callback=None):
        return self.fake_http_response()

#    def links(self, root, path):
#        return self.build_full_url(self.api_host, path)


#    def build_url(self, url, params=None):
#            return "/%d%s" % (API_VERSION, target_path)


#    def build_full_url(self, host, target):
#        return base_full_url + self.build_url(target)


#    def account(self, email='', password='', first_name='', last_name='', source=None):
#        return self.api_rest.POST(url, params, headers)

    
#    def thumbnail(self, root, from_path, size='small'):
#        return self.content_rest.request("GET", url, headers=headers, raw_response=True)


class DubnotesTests(unittest.TestCase):
    def setUp(self):
        self.client= DropboxClient("api_host", "content_host", "port", "auth", "token")
    
    def testGlobalData(self):
        DropboxClient.set_demo_data("default_fake_data")
        assert DropboxClient.data == "default_fake_data"
    
    def testGlobalStatus(self):
        DropboxClient.set_demo_status(1004)
        assert DropboxClient.status == 1004
    
    def testHTTPRespone(self):
        DropboxClient.set_demo_status(202)
        DropboxClient.set_demo_data("some data")
        resp = self.client.put_file("root", "to_path", "file_obj")
        assert isinstance(resp, FakeHTTPResponse)
        assert resp.read() == "some data"
        assert resp.status == 202
        