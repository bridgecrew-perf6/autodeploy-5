#!/usr/bin/python3

from typing import Union, Dict, Any

import json
import hmac
import hashlib
import configparser


class WebhookOutput(object):

    config: str = '/etc/autodeploy.cfg'

    def __init__(self, data: Union[str, bytes]):
        if isinstance(data, str):
            self.data = data.encode('utf8')
        else:
            self.data = data

        self.cfg = configparser.ConfigParser()
        self.cfg.read_file(self.config)
        self._processed_json: Dict[Any, Any] = dict()

    def check_signature(self, secret: str, signature: str) -> bool:
        h = hmac.new(secret.encode('utf8'), digestmod=hashlib.sha256)
        return hmac.compare_digest(h.hexdigest(), signature)

    # The json from the webhook should always be a dictionary, not a list
    @property
    def json(self) -> Union[dict, None]:
        if not self._processed_json:
            self._processed_json = json.loads(self.data)
        return self._processed_json

    @property
    def cfgsection(self) -> dict:
        return dict(self.cfg[self.json['full_name']].items())

    def allowed_repo(self):
        return self.cfg.has_section(self.json['full_name'])

    def validate(self):
        if not self.allowed_repo():
            return False

    def notify_daemon(self):
        raise NotImplementedError()
