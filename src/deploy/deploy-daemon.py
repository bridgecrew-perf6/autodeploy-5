#!/usr/bin/python3

import redis
import time
import logging

from racflib.lock import wait_lock, unlock
from racflib.gitrepo import GitRepo, GitExcept
from racflib.proc import get_output
from racflib.mail import send_email


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('ktisync')

# Check out with root's id_rsa key as a deploy key in gitea:
# location: git@githost01.sdcc.bnl.gov:SDCC/lfkti.git
REPO = '/usr/src/kti/'
URL = 'git@githost01.sdcc.bnl.gov:SDCC/lfkti.git'
LOCK = '/var/lock/ktisync.lock'
DEPLOY = '/farm/kti/7'


if __name__ == "__main__":
    r = redis.Redis()
    git = GitRepo(REPO, URL)
    while True:
        try:
            rawrec = r.brpop("kti", 15)
            if not rawrec:
                continue
            branch, oldhash, newhash = rawrec[1].split(':')
            email = r.get(newhash)
        except (LookupError, ValueError, AttributeError):
            time.sleep(0.1)
            log.info("Bad field read from redis {0}".format(rawrec))
            continue

        fd = wait_lock(LOCK)
        try:
            git.fetch()
            current_hash = git.current_state(git.current_ref('master'))
            if oldhash != current_hash:
                log.warning("Repo in unexpected state (%s) != upstream (%s)",
                            current_hash, oldhash)
                log.warning("Will reset to new state regardless...")
            git.reset(newhash)
        except GitExcept as e:
            log.error("Exception with git: %s", e)
            send_email('willsk@bnl.gov', 'KTI-sync', str(e), 'kti-sync@imgsvr')
        else:
            out, rc = get_output('kti -v .', cwd='/farm/kti/7')
            msg = """
Hello,

KTI sync ran successfully on imgsvr and master barnch is now
in state %s updating files:

%s
""" % (newhash, out)
            # TODO: Enable real sync when master
            # _, r = get_output('kti-sync.sh')
            if email:
                send_email(email, 'KTI sync', msg, 'kti-sync@imgsvr')

        unlock(fd)
        email = None
