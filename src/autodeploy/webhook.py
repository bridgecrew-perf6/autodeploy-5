# Analyze a Gitea repository's webhook data (json) and check the signature and
# if the repo and branch combo is valid

from typing import AnyStr

import json
import logging

from . import config
from .util import check_hmac

log = logging.getLogger(__name__)

__all__ = ['check_webhook_output']


def check_webhook_output(data: bytes, signature: str) -> bool:
    try:
        js = json.loads(data)
    except json.JSONDecodeError:
        log.exception("Invalid JSON!")
        return False

    repo = js['repository']['fullname']

    # Allowed repos are cfgfile section names
    if not config.has_section(repo):
        log.warning('Not an allowed repo: %s', repo)
        return False
    cfg = config[repo]

    # Validate signature
    if not check_hmac(data, cfg['secret'], signature):
        log.warning('Invalid signature detected on request for %s - %s', repo, js['ref'])
        return False

    # Check branch (depends on cfg[bare] which would allow all branches)
    if cfg.getboolean('bare', False):
        return True
    elif js['ref'] == f"refs/heads/{js['branch']}":
        log.debug('Not an allowed branch on %s: %s', repo, js['ref'])
        return False

    return True
