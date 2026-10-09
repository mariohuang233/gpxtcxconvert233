"""Serve the built site under a project prefix to catch Pages path regressions."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import os

PREFIX='/gpxtcxconvert233'
SITE=Path(__file__).resolve().parents[1]/'_site'

class PagesHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path=urlsplit(self.path).path
        if path==PREFIX:
            self.send_response(302);self.send_header('Location',PREFIX+'/');self.end_headers();return
        if not path.startswith(PREFIX+'/'):
            self.send_error(404);return
        super().do_GET()

    def translate_path(self,path):
        return super().translate_path(path[len(PREFIX):])

ThreadingHTTPServer(('127.0.0.1',int(os.environ.get('PAGES_TEST_PORT',8900))),partial(PagesHandler,directory=str(SITE))).serve_forever()
