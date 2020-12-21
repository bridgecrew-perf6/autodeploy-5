#!/usr/bin/env python3

from autodeploy import socket_path
from autodeploy.util import run_serverclass_thread
from autodeploy.webhook import WebhookOutput
from autodeploy.message import encode_message, send_message


from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

log = logging.getLogger(__name__)


class WebhookHTTPRequestHandler(BaseHTTPRequestHandler):

    # Default error sends HTML
    def answer(self, code, msg, body=''):
        self.send_response(code, msg)
        self.send_header('Connection', 'close')
        self.send_header("Content-Type", 'text/plain;charset=utf8')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body.encode('utf8'))
        else:
            self.wfile.write(msg.encode('utf8'))

    def do_POST(self):

        postlen = int(self.headers['content-length'])
        webdata = self.rfile.read(postlen)
        log.debug("Got %d bytes in request from %s", postlen, self.client_address)
        sig = self.headers['X-Gitea-Signature']

        if not sig:
            self.answer(401, 'No signature provided')
            return
        try:
            self.process_data(webdata, sig)
        except Exception as e:
            log.exception('Unexpected error processing request')
            self.answer(500, 'Error processing request', str(e) + '\n')

    def process_data(self, json, signature):
        data = WebhookOutput(json, signature)
        if not data.validate():
            self.answer(403, 'Invalid signature or repo')
            return
        msgpkt = encode_message(data.json, data.cfg['secret'])
        response, ok = send_message(msgpkt, socket_path)
        log.info("Daemon success == %s", ok)
        if not ok:
            self.answer(500, 'Error processing repo', response)
        else:
            self.answer(200, 'Git repo sync OK', response)


if __name__ == "__main__":
    server_address = ('', 5000)
    run_serverclass_thread(HTTPServer(server_address, WebhookHTTPRequestHandler))
