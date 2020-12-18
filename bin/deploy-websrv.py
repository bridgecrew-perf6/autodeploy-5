
from autodeploy.util import run_serverclass_thread
from autodeploy.webhook import WebhookOutput

from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

log = logging.getLogger(__name__)

class WebhookHTTPRequestHandler(BaseHTTPRequestHandler):

    error_content_type = 'text/plain;charset=utf-8'

    def do_POST(self):
        webdata = self.rfile.read()
        log.info("WD: %s\nH: %s", webdata, self.headers)
        sig = self.headers['X-Gitea-Signature']
        if not sig:
            self.send_error(401, 'No signature provided')
            return
        data = WebhookOutput(webdata, sig)
        if not data.validate():
            self.send_error(403, 'Invalid signature or repo')
            return
        response, ok = data.notify_daemon()
        if not ok:
            self.send_error(500, response)
        else:
            self.end_headers()
            self.wfile(response)


if __name__ == "__main__":
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, WebhookHTTPRequestHandler)
    httpd.serve_forever()
