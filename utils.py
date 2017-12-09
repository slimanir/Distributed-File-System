import json
import os.path
from contextlib import closing
from httplib import HTTPConnection


class memoize:

    def __init__(self, fn):

        self.fn = fn
        self.cache = {}

    def __call__(self, *args, **kwds):


        key = tuple(args) + tuple(kwds)

        if key in self.cache:
            return self.cache[key]

        ans = self.fn(*args, **kwds)
        return self.cache.setdefault(key, ans)

    def renew(self, *args, **kwds):

        key = tuple(args) + tuple(kwds)

        if key in self.cache:
            del self.cache[key]

        return self(*args, **kwds)


def load_config(config, filepath):

    if not os.path.exists(filepath):
        return

    with open(filepath) as f:
        c = json.loads(f.read())
        config.update(c)


def get_host_port(s):

    host, port = s.split(':')
    return host, int(port)


def is_locked(filepath, host, port, lock_id=None):

    with closing(HTTPConnection(host, port)) as con:
        if lock_id is not None:
            filepath += '?lock_id=%s' % lock_id

        con.request('GET', filepath)

        r = con.getresponse()

    return r.status != 200


@memoize
def get_server(filepath, host, port):

    with closing(HTTPConnection(host, port)) as con:
        con.request('GET', filepath)
        response = con.getresponse()
        status, srv = response.status, response.read()

    if status == 200:
        return srv

    return None


def get_lock(filepath, host, port):

    with closing(HTTPConnection(host, port)) as con:
        con.request('POST', filepath)
        response = con.getresponse()
        status = response.status

        if status != 200:
            raise Exception('Unable to grant lock on %s.' % filepath)

        lock_id = response.read()

    return lock_id


def revoke_lock(filepath, host, port, lock_id):

    with closing(HTTPConnection(host, port)) as con:
        con.request('DELETE', filepath + ('?lock_id=%d' % int(lock_id)))
        response = con.getresponse()

    if response.status != 200:
        raise Exception('Unable to revoke lock on %s.' % filepath)
