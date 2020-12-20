#!/usr/bin/python3

from typing import Union, Dict, Any, Tuple  # noqa

import json
import hmac
import socket

from .message import encode_message
from . import config

import logging
log = logging.getLogger(__name__)


class WebhookOutput(object):

    def __init__(self, data: Union[str, bytes], signature: str):
        if isinstance(data, str):
            self.data = data.encode('utf8')
        else:
            self.data = data
        self.cfg = config
        self.sig = signature

    # The json from the webhook should always be a dictionary, not a list
    @property
    def json(self) -> dict:
        if not hasattr(self, '_processed_json'):
            self._processed_json = json.loads(self.data)
        return self._processed_json

    @property
    def reponame(self) -> str:
        return self.json['repository']['full_name']

    @property
    def cfgsection(self):
        """ Return the section in the config-structure for current repo """
        if not hasattr(self, '_cfgsec'):
            self._cfgsec = self.cfg[self.reponame]
        return self._cfgsec

    # Make sure is called before self.cfgsection!
    def _allowed_repo(self) -> bool:
        return self.cfg.has_section(self.reponame)

    def _allowed_branch(self) -> bool:
        # all branches "allowable" on a bare repo
        if self.cfgsection.getboolean('bare', False):
            return True
        # otherwise check branch against config file
        return self.json['ref'] == f"refs/heads/{self.cfgsection['branch']}"

    def _good_signature(self, secret: str, signature: str) -> bool:
        h = hmac.new(secret.encode('utf8'), self.data, digestmod='sha256')
        return hmac.compare_digest(h.hexdigest(), signature)

    def validate(self) -> bool:
        if not self._allowed_repo():
            log.warning('Not an allowed repo: %s', self.reponame)
            return False
        if not self._allowed_branch():
            log.debug('Not an allowed branch on %s: %s', self.reponame, self.json['ref'])
            return False
        if not self._good_signature(self.cfgsection['secret'], self.sig):
            log.warning('Invalid signature detected on request for %s - %s',
                        self.reponame, self.json['ref'])
            return False
        return True

    def notify_daemon(self) -> Tuple[str, bool]:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.connect(self.cfgsection['socket'])
            msg_bytes = encode_message(self.json, self.cfgsection['secret'])
            s.sendall(msg_bytes)
            s.shutdown(socket.SHUT_WR)
            data = b''
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
            ans = data.decode('utf8')
        ok = True
        if ans.split('\n')[0] != "OK":
            ok = False
        return ans, ok
