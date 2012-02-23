import os, cgi
import StringIO
import datetime
import urllib

if os.environ.has_key('DUBNOTES_DEBUG'):
    from fake_dropbox import client, rest, auth
else:
    from dropbox import client, rest, auth

class ActionFactory(object):
    @staticmethod
    def create(action, notename, request, session):
        if action == 'edit':
            return EditAction(notename, session)
        elif action == 'new':
            return NewAction(session)
        elif action == 'delete':
            return DeleteAction(notename, session)
        elif action == 'save':
            return SaveAction(request, session)
            pass
        return ListAction(session)


class Action(object):
    def __init__(self, session):
        self.session = session
        conf = self.session.config
        self.dropbox_client = client.DropboxClient(conf['server'], conf['content_server'],
                                                   conf['port'], self.session.dropbox_auth, self.session.access_token)
        
    def do(self):
        pass

 
 
class EditAction(Action):
    def __init__(self, notename, session):
        self.notename = notename
        self.filename = ""
        self.content = ""
        super(EditAction, self).__init__(session)
    
    def build_edit_template(self):
        return {
                 'user': self.session.user.uid,
                 'token': self.session.request_token.req_key,
                 'content': self.content,
                 'file': self.filename,
                 'displayname': os.path.basename(self.filename)
                }

    def render(self):
        if self.filename != '':
             f = self.dropbox_client.get_file (self.session.config['root'], self.filename)
             self.content = f.read()
             f.close()
        template_values = self.build_edit_template()
        path = os.path.join(os.path.dirname(__file__), 'editpage.html')
        return (path, template_values)
    
    def do(self):
        self.filename = self.session.config["dubnotes_folder"] + "/" + urllib.unquote(self.notename)
        return self.render()
        
              
class ListAction(Action):
    def __init__(self, session):
        super(ListAction, self).__init__(session)

    def build_list_template(self):
        file_list =  [[cgi.escape(x["path"]), os.path.basename(x["path"])] for x in self.resp.data['contents'] if not x['is_dir']]
        return {
            'user': self.session.user.uid,
            'token': self.session.request_token.req_key,
            'files': file_list,
        }

    def render(self):
        # Build list of files and folders
        self.resp = self.dropbox_client.metadata(self.session.config['root'], self.session.config['dubnotes_folder'])
        
        #TODO create folder if folder does not exist
        #if resp.status == 404:
        #  self.create_new_file()
          
        # {u'error': u'Access token is disabled.'} Status: 500 Internal Server Error Content-Type: text/html; charset=utf-8 Cache-Control: no-cache Expires: Fri, 01 Jan 1990 00:00:00 GMT Content-Length: 0 
        # alle nicht abgefangenen error codes aeussern sich in KeyError ('contents') dump
        template_values = self.build_list_template()
        
        path = os.path.join(os.path.dirname(__file__), 'mainpage.html')
        return (path, template_values)
    
    def do(self):
        return self.render()
              
                
class SaveAction(ListAction):
    def __init__(self, request, session):
        self.request = request
        super(SaveAction, self).__init__(session)

    def do(self):
        fname = self.request.get("file")
        showname = self.request.get("displayname")
        content = self.request.get("content")
        s = StringIO.StringIO(content.encode("utf-8"))
        if fname != '':
            folder, s.name = os.path.split(fname)
            f = self.dropbox_client.put_file (self.session.config['root'], folder, s)
            #self.response.out.write(f.status)
            if f.status != 200:
              pass
              # handle error
              
        # has the file be renamed?
        if fname != '' and os.path.basename(fname) != showname:
            folder, name = os.path.split(fname)
            f = self.dropbox_client.file_move (self.session.config['root'], fname, os.path.join(folder, showname))
            if f.status != 200:
              pass
              # could not rename
        return super(SaveAction, self).do()
 
 
class DeleteAction(ListAction):
    def __init__(self, notename, session):
        self.notename = notename
        super(DeleteAction, self).__init__(session)  
          
    def do(self):
        self.filename = self.session.config["dubnotes_folder"] + "/" + urllib.unquote(self.notename)
        self.dropbox_client.file_delete(self.session.config['root'], self.filename)
        return super(DeleteAction, self).do()
   
   
class NewAction(ListAction):
    def __init__(self, session):
        super(NewAction, self).__init__(session)  
    
    def create_new_file(self):
        ret = self.dropbox_client.metadata (self.session.config['root'], self.session.config['dubnotes_folder'])
        if ret.status == 403:
          self.dropbox_client.create_folder (self.session.config['root'], self.session.config['dubnotes_folder'])      
        s = StringIO.StringIO('')
        s.name = 'note_' + datetime.datetime.time(datetime.datetime.now()).isoformat().split('.')[0].replace(':', '_') + '.txt'
        f = self.dropbox_client.put_file (self.session.config['root'], self.session.config['dubnotes_folder'], s)
          
    def do(self):
        self.create_new_file()
        return super(NewAction, self).do()
