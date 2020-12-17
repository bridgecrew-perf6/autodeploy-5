import configparser
from socketserver import UnixDatagramServer, BaseRequestHandler

from .message import Message
from . import log, config


cfg = configparser.ConfigParser()
cfg.read_file(config)

class SyncRequest(BaseRequestHandler):

    config: str = config

    def setup(self):
        self.data, self.socket = self.request
        log.debug("Start reading from %s", self.client_address)

    def handle(self):
        msg = Message.from_msg(self.data)
        if not msg.repo in cfg:
            raise KeyError(f'Got a repo ({msg.repo}) not found in cfg=f{cfg}')

        sec = cfg[msg.repo]
        if not msg.verify(sec['secret'].encode('utf8')):
            raise ValueError(f'Invalid signature on {msg.repo}')








