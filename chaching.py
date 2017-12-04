import http.server
import hashlib
import os
import urllib
from urllib import urlopen

class CacheHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
      m = hashlib.sha256()
      m.update(self.path.encode('utf-8'))
      cache_filename = m.hexdigest() + ".cached"
      if os.path.exists(cache_filename):
          print ("Caching done")
          data = open(cache_filename).readlines()
      else:
          print ("Caching impossible ")
          data = urllib.urlopen("http:/" + self.path).readlines()
          open(cache_filename, 'wb').writelines(data)
      self.send_response(200)
      self.end_headers()
      self.wfile.writelines(data)

def run():
    server_address = ('', 8000)
    http_server = http.server.HTTPServer(server_address, CacheHandler)
    http_server.serve_forever()

if __name__ == '__main__':
    run()
