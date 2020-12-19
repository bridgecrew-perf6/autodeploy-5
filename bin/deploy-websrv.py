#!/usr/bin/env python3
from autodeploy.util import run_serverclass_thread
from autodeploy.webhook import WebhookOutput

from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

log = logging.getLogger(__name__)


class WebhookHTTPRequestHandler(BaseHTTPRequestHandler):

    # Default error sends HTML
    def send_error(self, code, msg, explain=''):
        self.send_response(code, msg)
        self.send_header('Connection', 'close')
        self.send_header("Content-Type", 'text/plain;charset=utf8')
        self.send_header("Content-Length", str(len(explain)))
        self.end_headers()
        if explain:
            self.wfile.write(explain.encode('utf8'))

    def do_POST(self):
        postlen = int(self.headers['content-length'])
        webdata = self.rfile.read(postlen)
        log.debug("Got %d bytes in request from %s", postlen, self.client_address)
        sig = self.headers['X-Gitea-Signature']
        if not sig:
            self.send_error(401, 'No signature provided')
            return
        try:
            self.process_data(webdata, sig)
        except Exception as e:
            log.exception('Unexpected error processing request')
            self.send_error(500, 'Error processing request', str(e) + '\n')

    def process_data(self, json, signature):
        data = WebhookOutput(json, signature)
        if not data.validate():
            self.send_error(403, 'Invalid signature or repo')
            return
        response, ok = data.notify_daemon()
        if not ok:
            self.send_error(500, 'Error processing repo', response)
        else:
            self.end_headers()
            self.wfile.write(response)


if __name__ == "__main__":
    server_address = ('', 5000)
    run_serverclass_thread(HTTPServer(server_address, WebhookHTTPRequestHandler))
