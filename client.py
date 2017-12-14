import utils
from contextlib import closing
from http.client import HTTPConnection
from tempfile import SpooledTemporaryFile


####### Is a distant file, it's stored in memory if it size if less than the max_size parameter, otherwise it's stored on the disk #####

class File(SpooledTemporaryFile):
    
###### filepath: the path of the distant file mode: take the same argument as mode argument of the global open() + optional flag c (which mean store in cache) #####

    def __init__(self, filepath, mode='rtc'):

        self.mode = mode
        self.filepath = filepath
        host, port = utils.get_host_port(_config['directoryserver'])
        self.srv = utils.get_server(filepath, host, port)

        if self.srv is None:
            raise IOError('Impossible to find a server that serve %s.'
                    % filepath)

        self.last_modified = None
        SpooledTemporaryFile.__init__(self, _config['max_size'], mode.replace('c', ''))

        host, port = utils.get_host_port(_config['lockserver'])
        if utils.is_locked(filepath, host, port):
            raise IOError('The file %s is locked.' % filepath)

        if 'w' not in mode:
            host, port = utils.get_host_port(self.srv)
            with closing(HTTPConnection(host, port)) as con:
                con.request('GET', filepath)
                response = con.getresponse()
                self.last_modified = response.getheader('Last-Modified')
                status = response.status

                if status not in (200, 204):
                    raise IOError('Error (%d) while opening file.' % status)

                if status != 204:
                    self.write(response.read())

                if 'r' in mode:
                    self.seek(0)

                self.lock_id = None
 ####### Automatically gets a lock if we're in write/append mode ######

        if 'a' in mode or 'w' in mode:
            host, port = utils.get_host_port(_config['lockserver'])
            self.lock_id = int(utils.get_lock(filepath, host, port))

        if 'c' in mode:
            File._cache[filepath] = self
#############  Close the file  ###############
    def __exit__(self, exc, value, tb):

        self.close()

        if 'c' not in self.mode:
            return SpooledTemporaryFile.__exit__(self, exc, value, tb)

        return False

    def close(self):

        self.flush()

        if 'c' not in self.mode:
            SpooledTemporaryFile.close(self)
#####  Flush the data to the server ######
    def flush(self):

        SpooledTemporaryFile.flush(self)
        self.commit()
       
##### Send the local file to the fileserver ######
    def commit(self):

        if 'a' in self.mode or 'w' in self.mode:
            self.seek(0)
            data = self.read()
            host, port = utils.get_host_port(self.srv)
            with closing(HTTPConnection(host, port)) as con:
                con.request('PUT', self.filepath + '?lock_id=%s' % self.lock_id,
                            data)

                response = con.getresponse()
                self.last_modified = response.getheader('Last-Modified')
                status = response.status
                if status != 200:
                    raise IOError('Error (%d) while committing change to'
                                     ' the file.' % status)

        if self.lock_id is not None:
            host, port = utils.get_host_port(_config['lockserver'])
            utils.revoke_lock(self.filepath, host, port, self.lock_id)
            
#### Retrieve a file from the cache in the filepath of the file ######

    @staticmethod
    def from_cache(filepath):

        if filepath in File._cache:
            f = File._cache[filepath]

            host, port = utils.get_host_port(_config['directoryserver'])
            fs = utils.get_server(filepath, host, port)
            host, port = utils.get_host_port(fs)

            with closing(HTTPConnection(host, port)) as con:
                con.request('HEAD', filepath)

                if (f.last_modified ==
                        con.getresponse().getheader('Last-Modified')):
                    f.seek(0)
                    return f
                else:
                    del File._cache[filepath]

        return None  ### The file isn't in the cache or if the cache expired

open = File

_config = {
        'directoryServer': None,
        'max_size': 1024 ** 2,
         } 
File._cache = {}
utils.load_config(_config, 'client.dfs.json')
