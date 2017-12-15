import web

import directoryserver

urls = (
        '(/.*)', 'directoryserver.directoryServer',
       )

app = web.application(urls, globals())


if __name__ == '__main__':
    app.run()
