import os, cgi
import StringIO
import datetime

class ActionFactory(object):
    @staticmethod
    def create(action, request, dropbox_client, session):
        if action == 'edit':
            return EditAction(request, dropbox_client, session)
        elif action == 'new':
            return NewAction(dropbox_client, session)
        elif action == 'delete':
            return DeleteAction(request, dropbox_client, session)
        elif action == 'save':
            return SaveAction(request, dropbox_client, session)
            pass
        return ListAction(dropbox_client, session)


class Action(object):
    def __init__(self, dropbox_client, session):
        self.dropbox_client = dropbox_client
        self.session = session
        
    def do(self):
        pass

 
class EditAction(Action):
    def __init__(self, request, dropbox_client, session):
        self.request = request
        self.filename = ""
        self.content = ""
        super(EditAction, self).__init__(dropbox_client, session)
    
    def build_edit_template(self):
        return {'delete_url':' /?uid=' + self.session.user.uid + '&oauth_token=' + self.session.request_token.req_key + '&fname=' + self.filename + '&action=delete',
                     'url':'/?uid=' + self.session.user.uid + '&oauth_token=' + self.session.request_token.req_key,
                     'content': self.content,
                     'fname': self.filename,
                     'showname': os.path.basename(self.filename)}

    def render(self):
        if self.filename != '':
             f = self.dropbox_client.get_file (self.session.config['root'], self.filename)
             self.content = f.read()
             f.close()
        template_values = self.build_edit_template()
        path = os.path.join(os.path.dirname(__file__), 'editpage.html')
        return (path, template_values)
    
    def do(self):
        self.filename = self.request.get("get")
        #TODO: raise if we do not have "get" in request  
        return self.render()
        
              
class ListAction(Action):
    def __init__(self, dropbox_client, session):
        super(ListAction, self).__init__(dropbox_client, session)

    def build_list_template(self):
        return {
            'files': [['/?uid=' + self.session.user.uid + '&oauth_token=' + self.session.request_token.req_key + '&action=edit&get=' + cgi.escape(x["path"]), 
                       os.path.basename(x["path"])] for x in self.resp.data['contents'] if not x['is_dir']],
            'new_url': '/?uid=' + self.session.user.uid + '&oauth_token=' + self.session.request_token.req_key + '&action=new',
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
    def __init__(self, request, dropbox_client, session):
        self.request = request
        super(SaveAction, self).__init__(dropbox_client, session)

    def do(self):
        fname = self.request.get("f_name")
        showname = self.request.get("f_showname")
        content = self.request.get("f_content")
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
    def __init__(self, request, dropbox_client, session):
        self.request = request
        super(DeleteAction, self).__init__(dropbox_client, session)  
          
    def do(self):
        self.dropbox_client.file_delete(self.session.config['root'], self.request.get('fname'))
        return super(DeleteAction, self).do()
   
   
class NewAction(ListAction):
    def __init__(self, dropbox_client, session):
        super(NewAction, self).__init__(dropbox_client, session)  
    
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
