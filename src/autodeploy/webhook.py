# Analyze a Gitea repository's webhook data (json) and check the signature and
# if the repo and branch combo is valid
from typing import Optional

import json
import logging

from . import config
from .util import check_hmac

log = logging.getLogger(__name__)

__all__ = ['process_webhook_output']


def process_webhook_output(data: bytes, signature: str) -> Optional[dict]:
    """ Parse the webhook data and validate it, returning the json if
        it is valid or None if not
    """
    try:
        js = json.loads(data)
    except json.JSONDecodeError:
        log.exception("Invalid JSON!")
        return None

    repo = js['repository']['full_name']

    # Allowed repos are cfgfile section names
    if not config.has_section(repo):
        log.warning('Not an allowed repo: %s', repo)
        return None
    cfg = config[repo]

    # Validate signature
    if not check_hmac(data, cfg['secret'], signature):
        log.warning('Invalid signature detected on request for %s - %s', repo, js['ref'])
        return None

    # Check branch (depends on cfg[bare] which would allow all branches)
    if cfg.getboolean('bare', False):
        return js
    elif js['ref'] != f"refs/heads/{cfg['branch']}":
        log.debug('Not an allowed branch on %s: %s', repo, js['ref'])
        return None

    return js
