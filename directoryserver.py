import atexit
import logging
import os
import shelve
import web
import utils

############## Responsible of mapping file servers and directories  ################

class directoryServer:

############### The server that holds the directory   ####################

    def GET(self, filepath):
        
############ Return a server which has the directory where the filepath is located #########

        web.header('Content-Type', 'text/plain; charset=UTF-8')
        filepath = str(filepath)

        if filepath == '/':
            return '\n'.join('%s=%s' % (dirpath, _names[dirpath])
                    for dirpath in sorted(_names))

        dirpath = str(os.path.dirname(filepath))

        if dirpath in _names:
            return _names[dirpath]

        raise web.notfound('No file server serve this file.')

    
########### POST = Update when 'add' is 'True' ############## 

    def POST(self, dirpath):
        return _update(str(dirpath))
    
########### DELETE = Update when 'add' is 'True' ##############

    def DELETE(self, dirpath):
        
        return _update(str(dirpath), False)
    
######### Adding a pair of directory/server with to the directoryserver ########
    
def _update(dirpath, add=True):
    web.header('Content-Type', 'text/plain; charset=UTF-8')
    i = web.input()

    if 'srv' not in i:
        raise web.badrequest()

    srv = i['srv']

    if dirpath == '/':
        if 'dirs' not in i:
            raise web.badrequest()

        for dirpath in i['dirs'].split('\n'):
            if not dirpath:
                continue

            try:
                _update_names(dirpath, srv, add)
            except ValueError as e:
                logging.exception(e)

    else:
        try:
            _update_names(dirpath, srv, add)
        except ValueError as e:
            logging.exception(e)
####### Update the name dictionnary and the database #########    
def _update_names(dirpath, srv, add=True):


    if dirpath[-1] == '/':
        dirpath = os.path.dirname(dirpath)

    if add:
        logging.info('Update directory %s on %s.', dirpath, srv)
        _names[dirpath] = srv

    elif dirpath in _names:
        logging.info('Remove directory %s on %s.', dirpath, srv)
        del _names[dirpath]

    else:
        raise ValueError('%s wasn\'t not deleted, because it wasn\'t'
                         ' in the dictionnary/database.' % dirpath)


_config = {
            'dbfile': 'names.db',
         }

logging.info('Loading config file directoryServer.dfs.json.')
utils.load_config(_config, 'directoryServer.dfs.json')
_names = shelve.open(_config['dbfile'])

atexit.register(lambda: _names.close())
