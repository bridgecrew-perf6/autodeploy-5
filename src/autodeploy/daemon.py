from typing import Union

import socket
import configparser
import traceback
from socketserver import UnixDatagramServer, BaseRequestHandler

from .message import Message
from . import log, config

from .repo import GitRepo, GitExcept
from .util import get_output, send_email


cfg = configparser.ConfigParser()
cfg.read_file(config)

class SyncServer(UnixDatagramServer):
    pass

class SyncRequest(BaseRequestHandler):

    config: str = config

    def setup(self):
        self.data, self.socket = self.request
        log.debug("Start reading from %s", self.client_address)

    def do_request(self):
        msg = Message.from_msg(self.data)
        if not msg.repo in cfg:
            raise KeyError(f'Got a repo ({msg.repo}) not found in cfg=f{cfg}')

        sec = cfg[msg.repo]
        if not msg.verify(sec['secret'].encode('utf8')):
            raise ValueError(f'Invalid signature on {msg.repo}')
        make_repo_state(msg, sec['local'], sec['url'], sec.get('postscript'))

    def handle(self):
        try:
            self.do_request()
        except Exception as e:
            log.warning("Exception while handling request: %s", e)
            self.socket.sendto(str(e).encode('utf8'), self.client_address)



def make_repo_state(m: Message, path: str, url: str, postscript: Union[str, None]) -> bool:
    git = GitRepo(path, url)
    try:
        git.fetch()
        current_hash = git.current_state(git.current_ref('master'))
        if m.before != current_hash:
            log.warning("Repo in unexpected state (%s) != upstream (%s)",
                        current_hash, m.before)
            log.warning("Will reset to new state regardless...")
        git.reset(m.state)
    except GitExcept as e:
        log.error("Exception with git: %s", e)
        send_email(m.email, f'Git Deploy Failure for {m.repo}', str(e))
    else:
        msg = f"""
Hello,

Git Deploy was done for {m.repo} on {socket.getfqdn()} in {path}
setting state {m.state} for branch {m.branch}.
"""
        if postscript:
            out, rc = get_output(postscript)
            msg += f'\nPost-script {postscript} returned {rc}:\n{out}'
        msg += '\nGitDeploy Daemon'

        subject = f'Git Deploy Done for {m.repo} on {socket.getfqdn()}'
        send_email(m.email, subject, msg)

    return False







