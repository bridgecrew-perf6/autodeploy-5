# Represent the output of a Gitea repository's webhook data (json) and the
# signature (from the header) as an object that can be verified against the
# config file.

from typing import AnyStr

import json
import hmac
import logging

from . import config


log = logging.getLogger(__name__)


class WebhookOutput(object):
    """ Object representing a processed JSON document from the output of
        a Gitea webhook that does the verification of the signature and
        allowed-repos from the config-file.
    """

    def __init__(self, data: AnyStr, signature: str):
        if isinstance(data, str):
            self.data = data.encode('utf8')
        else:
            self.data = data
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
    def cfg(self):
        """ Return the section in the config-structure for current repo """
        if not hasattr(self, '_cfgsec'):
            self._cfgsec = config[self.reponame]
        return self._cfgsec

    # Make sure is called before self.cfg!
    def _allowed_repo(self) -> bool:
        return config.has_section(self.reponame)

    def _allowed_branch(self) -> bool:
        # all branches "allowable" on a bare repo
        if self.cfg.getboolean('bare', False):
            return True
        # otherwise check branch against config file
        return self.json['ref'] == f"refs/heads/{self.cfg['branch']}"

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
        if not self._good_signature(self.cfg['secret'], self.sig):
            log.warning('Invalid signature detected on request for %s - %s',
                        self.reponame, self.json['ref'])
            return False
        return True
