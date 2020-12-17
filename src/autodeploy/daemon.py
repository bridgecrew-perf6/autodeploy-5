from socketserver import UnixDatagramServer, BaseRequestHandler

log = logging.getLogger('autodeploy-daemon')

class SyncRequest(BaseRequestHandler):

    def handle(self):
        self.request
