import web

import lockserver

urls = (
        '(/.*)', 'lockserver.LockServer',
       )

app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
