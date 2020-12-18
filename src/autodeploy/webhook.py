#!/usr/bin/python3

from typing import Union, Dict, Any  # noqa

import json
import hmac
import socket
import configparser

from .message import Message, encode_message
from . import log, config

def validate_hmac(secret: str, signature: str) -> bool:
    h = hmac.new(secret.encode('utf8'), digestmod='sha256')
    return hmac.compare_digest(h.hexdigest(), signature)


class WebhookOutput(object):

    def __init__(self, data: Union[str, bytes], signature: str):
        if isinstance(data, str):
            self.data = data.encode('utf8')
        else:
            self.data = data

        self.cfg = configparser.ConfigParser()
        self.cfg.read_file(config)
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
            self._cfgsec = dict(self.cfg[self.json['full_name']].items())
        return self._cfgsec

    # Make sure is called before self.cfgsection!
    def allowed_repo(self) -> bool:
        return self.cfg.has_section(self.json['full_name'])

    def allowed_branch(self) -> bool:
        # all branches "allowable" on a bare repo
        if self.cfgsection.get('bare', False):
            return True
        # otherwise check branch against config file
        return self.json['ref'] == f"refs/heads/{self.cfgsection['branch']}"

    def validate(self) -> bool:
        if self.allowed_repo() and self.allowed_branch():
            return validate_hmac(self.cfgsection['secret'], self.sig)
        return False

    def notify_daemon(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        msg_bytes = encode_message(self.json, self.cfgsection['secret'])
        n = s.sendto(msg_bytes, self.cfgsection['socket'])
        ans = s.recvfrom(1024).decode('utf8')
        if ans != "OK":
            log.error("Failed to notify daemon: %s", ans)
        # TODO: Send email?
