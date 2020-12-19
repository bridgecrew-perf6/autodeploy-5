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
    def cfgsection(self) -> dict:
        """ Return the section in the config-structure for current repo """
        if not hasattr(self, '_cfgsec'):
            self._cfgsec = dict(self.cfg[self.json['repository']['full_name']].items())
        return self._cfgsec

    # Make sure is called before self.cfgsection!
    def _allowed_repo(self) -> bool:
        return self.cfg.has_section(self.json['repository']['full_name'])

    def _allowed_branch(self) -> bool:
        # all branches "allowable" on a bare repo
        if self.cfgsection.get('bare', False):
            return True
        # otherwise check branch against config file
        return self.json['ref'] == f"refs/heads/{self.cfgsection['branch']}"

    def _good_signature(self, secret: str, signature: str) -> bool:
        log.debug("validate hmac %s -> %s", secret, signature)
        h = hmac.new(secret.encode('utf8'), digestmod='sha256')
        h.update(self.data)
        return hmac.compare_digest(h.hexdigest(), signature)

    def validate(self) -> bool:
        if not self._allowed_repo():
            log.debug('not allowed repo: %s', self.json['repository']['full_name'])
            return False
        if not self._allowed_branch():
            log.debug('not allowed repo: %s', self.json['ref'])
            return False
        return self._good_signature(self.cfgsection['secret'], self.sig)

    def notify_daemon(self) -> Tuple[str, bool]:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        msg_bytes = encode_message(self.json, self.cfgsection['secret'])
        s.sendto(msg_bytes, self.cfgsection['socket'])
        ans = s.recv(4096).decode('utf8')
        ok = True
        if ans.split('\n')[0] != "OK":
            ok = False
        return ans, ok
