from typing import Union

import socket
import logging
from socketserver import UnixDatagramServer, DatagramRequestHandler

from .message import Message
from . import config

from .repo import GitRepo, GitExcept
from .util import get_output, send_email

log = logging.getLogger(__name__)

email = 'smtp_addr' in config['DEFAULT']


class SyncRequestHandler(DatagramRequestHandler):

    def do_request(self):
        log.debug("Start reading from %s", self.client_address)
        msg = Message.from_msg(self.packet)
        if msg.repo not in config:
            raise KeyError(f'Got a repo ({msg.repo}) not found in cfg=f{config}')

        sec = config[msg.repo]
        if not msg.verify(sec['secret'].encode('utf8')):
            raise ValueError(f'Invalid signature on {msg.repo}')

        try:
            make_repo_state(sec['local'], sec['url'], msg.before, msg.state)
        except GitExcept as e:
            log.exception("Exception with git: %s", e)
            raise
        else:
            run_postscript_and_notify(msg, sec['local'], sec.get('postscript'))

    def handle(self):
        try:
            self.do_request()
        except Exception as e:
            log.warning("Exception while handling request: %s", e)
            self.socket.sendto(str(e).encode('utf8'), self.client_address)
        else:
            self.socket.sendto(b'OK', self.client_address)


def make_repo_state(path: str, url: str, oldhash: str, newhash: str) -> None:
    """ Make sure git repo from @url is in state @newhash in folder @path """
    git = GitRepo(path, url)
    git.fetch()
    current_hash = git.current_state(git.current_ref('master'))
    if oldhash != current_hash:
        log.warning("Repo in unexpected state (%s) != upstream (%s)",
                    current_hash, oldhash)
        log.warning("Will reset to new state regardless...")
    git.reset(newhash)


def run_postscript_and_notify(m: Message, path: str, script: Union[str, None]):

    msg = f"""
Hello,

Git Deploy was done for {m.repo} on {socket.getfqdn()} in {path}
setting state {m.state} for branch {m.branch}.
"""
    if script:
        out, rc = get_output(f'{script} "{path}"')
        msg += f'\nPost-script {script} returned {rc}:\n{out.decode("utf8")}'
    msg += '\nGitDeploy Daemon'

    subject = f'Git Deploy Done for {m.repo} on {socket.getfqdn()}'
    if email:
        send_email(m.email, subject, msg)


class SyncServer(UnixDatagramServer):
    allow_reuse_address = True

    def __init__(self):
        super().__init__(config['DEFAULT']['socket'], SyncRequestHandler)
