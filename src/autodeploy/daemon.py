# Server that receives a signed compact "message" class that will put a gitrepo
# locally into such a state as is contained in the message

from typing import Union

import socket
import logging
from socketserver import UnixStreamServer, BaseRequestHandler

from .message import Message
from . import config

from .repo import GitRepo, GitExcept
from .util import get_output, send_email

log = logging.getLogger(__name__)

email = 'smtp_addr' in config['DEFAULT']


class SyncRequestHandler(BaseRequestHandler):

    def setup(self):
        self.data = b''
        while True:
            chunk = self.request.recv(4096)
            if not chunk:
                break
            self.data += chunk

    def do_request(self) -> bytes:
        # Already read all data in to self.data at this point
        log.debug("Daemon got raw data: %s", self.data)
        try:
            msg = Message.from_msg(self.data)
        except Exception as e:
            raise ValueError('Error decoding message / invalid message sent') from e

        if msg.repo not in config:
            raise KeyError(f'Got a repo ({msg.repo}) not found in cfg=f{config}')

        sec = config[msg.repo]
        if not msg.verify(sec['secret'].encode('utf8')):
            raise ValueError(f'Invalid signature on {msg.repo}')

        try:
            make_repo_state(sec['local'], sec['url'], msg.before, msg.state)
            log.info("GitRepo at %s synced %s --> %s by %s <%s>",
                     sec['local'], msg.before, msg.state, msg.fullname, msg.email)
        except GitExcept as e:
            log.exception("Exception with git: %s", e)
            raise
        return run_postscript_and_notify(msg, sec['local'], sec.get('postscript'))

    def handle(self):
        try:
            data = self.do_request()
        except Exception as e:
            log.error("Exception while handling request: %s", e)
            self.request.sendall(str(e).encode('utf8'))
        else:
            self.request.sendall(b'OK\n' + data)


def make_repo_state(path: str, url: str, oldhash: str, newhash: str) -> None:
    """ Make sure git repo from @url is in state @newhash in folder @path """
    git = GitRepo(path, url)
    git.fetch()
    current_hash = git.current_state('HEAD')
    if oldhash != current_hash:
        log.warning("Repo in unexpected state (%s) != upstream (%s)",
                    current_hash, oldhash)
    git.reset(newhash)


def run_postscript_and_notify(m: Message, path: str, script: Union[str, None]) -> bytes:

    msg = f"""
Hello,

Git Deploy was done for {m.repo} on {socket.getfqdn()} in {path}
setting state {m.state} for branch {m.branch}.
"""
    out = b''
    if script:
        out, rc = get_output(f'{script} "{path}"')
        msg += f'\nPost-script {script} returned {rc}:\n{out.decode("utf8")}'
    msg += '\nGitDeploy Daemon'

    subject = f'Git Deploy Done for {m.repo} on {socket.getfqdn()}'
    if email:
        send_email(m.email, subject, msg)
    return out


class SyncServer(UnixStreamServer):
    allow_reuse_address = True

    def __init__(self):
        super().__init__(config['DEFAULT']['socket'], SyncRequestHandler)
