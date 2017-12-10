import web
import utils
import atexit
import collections
import copy
import datetime
import logging
import os.path
import random
import shelve

Lock = collections.namedtuple('Lock', 'lock_id granted last_used')

############## Responsible of locking files  ################

class LockServer:
    #### LockServer is responsible of handling locking on files  #####
    
    def GET(self, filepath):


        web.header('Content-Type', 'text/plain; charset=UTF-8')
        filepath = str(filepath)
        i = web.input()
######## Print the list of files ##########
        if filepath == '/':
            return '\n'.join('%s=(%s, %s)' % (filepath,
                   str(_locks[filepath].granted),
                   str(_locks[filepath].last_used),)
                   for filepath in sorted(_locks))
        
#### File not locked then it's OK #######

        elif filepath not in _locks and 'lock_id' not in i:
            return 'OK'
###### File locked #######
        elif 'lock_id' in i:
            lock = _locks.get(filepath, -1)
            try:
                if int(i['lock_id']) == lock.lock_id:

                    _update_lock(filepath)
                    return 'OK' ### Lock id correct 
                else:
                    raise Exception("Bad lock_id") ### Lock id not correct 

            except (Exception, ValueError) as e:
                _revoke_lock(filepath) ### logging.exception 
                raise web.conflict()

        elif _lock_expired(filepath):

            _revoke_lock(filepath)
            return 'OK'
        raise web.conflict() 


    def POST(self, filepath):

        web.header('Content-Type', 'text/plain; charset=UTF-8')
        filepath = str(filepath)

        if filepath == '/':
            granted_locks = {} # get a lock for all filepaths in the request data

            for filepath in web.data().split('\n'): # allow an empty line at the end of the request
                if not filepath:
                    continue    

                try:
                    granted_locks[filepath] = _grant_new_lock(filepath) 
                except Exception as e:
                    logging.exception(e)

                    # revoking all previoulsy allocated locks
                    for filepath in granted_locks:
                        _revoke_lock(filepath)

                    raise web.unauthorized()

            return '\n'.join('%s=%d' % (filepath, lock_id,)\
                    for filepath, lock_id in granted_locks.items()) #list of filename is lock_id

        try:
            return _grant_new_lock(filepath) 
        except Exception as e:
            logging.exception(e)
            raise web.unauthorized() 


    def DELETE(self, filepath):

        web.header('Content-Type', 'text/plain; charset=UTF-8')

        filepath = str(filepath)
        i = web.input()
#### allow deletion of multiple locks
        if filepath == '/':
            if 'filepaths' not in i or 'lock_ids' not in i:
                raise web.badrequest()

            for filepath, lock_id in\
                    zip(i['filepaths'].split('\n'), i['lock_ids'].split('\n')):
                if _locks[filepath].lock_id == int(lock_id):
                    _revoke_lock(filepath) #revoke locks (lock ids associated with filepaths
####### regardless the lock id return OK, if's lock id is correct then revoke lock if it's not correct just say OK. ############
            return 'OK'

        elif filepath in _locks:
            if 'lock_id' in i:
                lock_id = i['lock_id']

                if _locks[filepath].lock_id == int(lock_id):
                    _revoke_lock(filepath) #revoke the lock associated to filename

                return 'OK'

            raise web.badrequest()

        else:
            return 'OK'

##### Lock expired after exceeding the lock_lifetime #####
def _lock_expired(filepath):

    last_used = _locks[filepath].last_used
    return (datetime.datetime.now() - last_used).seconds\
            > _config['lock_lifetime']

###### Grant a new lock, return its id and revoke the old one ###### 
def _grant_new_lock(filepath):

    if filepath in _locks:
        if not _lock_expired(filepath):
            raise Exception('Unable to grant a new lock (%s).' % filepath)

        _revoke_lock(filepath)

    return _new_lock(filepath)

###### Create a new lock for filepath and return its id #####
def _new_lock(filepath):

    lock_id = random.randrange(0, 32768)
    logging.info('Granting lock (%d) on %s.', lock_id, filepath)
    t = datetime.datetime.now()
    _locks[filepath] = Lock(lock_id, t, t)

    return lock_id

###### Update the last_used fields of lock to now ######
def _update_lock(filepath):

    t = datetime.datetime.now()

    logging.info('Update lock on %s from %s to %s.',
                 filepath, _locks[filepath].last_used, t)

    l = _locks[filepath]
    l = Lock(l.lock_id, l.granted, t)
    _locks[filepath] = l

#### Revoking the lock associated to filepath ######
def _revoke_lock(filepath):

    if filepath in _locks:
        logging.info('Revoking lock on %s.', filepath)
        del _locks[filepath]


_config = {
            'dbfile': 'locks.db',
            'lock_lifetime': 60,
         }

logging.info('Loading config file lockserver.dfs.json.')
utils.load_config(_config, 'lockserver.dfs.json')
_locks = shelve.open(_config['dbfile'])

atexit.register(lambda: _locks.close())
