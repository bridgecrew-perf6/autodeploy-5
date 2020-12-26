# A standalone web server that takes a Gitea webhook POST request and sends it
# to a running deploy-daemon locally. Contrast with deploy-cgi.py for a version
# that runs as a CGI script under an existing webserver. They do the same thing
# but this has a standalone server.

from autodeploy.util import run_serverclass_thread
from autodeploy.webhook import check_webhook_output
from autodeploy.message import Message, send_message


from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
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

        if not check_webhook_output(json, signature):
            self.answer(403, 'Invalid signature or repo')
            return
        response, ok = send_message(Message.from_json(json).as_bytes())
        log.info("Daemon success == %s", ok)
        if not ok:
            self.answer(500, 'Error processing repo', response)
        else:
            self.answer(200, 'Git repo sync OK', response)


class WebhookRecvServer(HTTPServer):
    def __init__(self, port):
        super().__init__(('', port), WebhookHTTPRequestHandler)


def daemon_main():
    port = 5000
    if '-p' in sys.argv:
        port = int(sys.argv[sys.argv.index('-p') + 1])
    run_serverclass_thread(WebhookRecvServer(port))
