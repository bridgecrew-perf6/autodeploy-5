# Server that receives a signed compact "message" class that will put a gitrepo
# locally into such a state as is contained in the message. The message is an
# already-digested summary of the Webhook output that the client to this server
# has validated and processed into a message. This server's job is to enact the
# changes.
#
# The reason for having two components is that the public-facing one can run in
# a different security context -- like as apache in a CGI script -- and this
# daemon can run as root or another user who will actually own the files in the
# end...

from typing import Optional, Union

import socket
import logging
import stat
import os

from socketserver import UnixStreamServer, BaseRequestHandler

from .message import Message
from . import config, mail_host

from .repo import GitRepo, GitExcept
from .util import get_output, send_email, run_serverclass_thread

log = logging.getLogger(__name__)

email = mail_host is not None


class SyncRequestHandler(BaseRequestHandler):

    # Overwrite parent setup to read input for us since we are message-based
    def setup(self):
        self.data = b''
        while True:
            chunk = self.request.recv(4096)
            if not chunk:
                break
            self.data += chunk

    # Handle method does the actual work and sends reponse back to client
    def handle(self):
        try:
            data = self.do_request()
        except Exception as e:
            log.error("Exception while handling request: %s", e)
            self.request.sendall(str(e).encode('utf8'))
        else:
            self.request.sendall(b'OK\n' + data)

    def do_request(self) -> bytes:
        """ Dispatch the request by putting repo in the requested state,
            returning any output of the postscript if available, and raising
            an exception on any errors
        """

        # Already read all data in to self.data at this point
        log.debug("Daemon got raw data: %s", self.data)
        try:
            msg = Message.from_bytes(self.data)
        except Exception as e:
            raise ValueError('Error decoding / invalid message sent') from e

        # Section names in the config file are repo names
        if msg.repo not in config:
            raise KeyError(f'Got a repo ({msg.repo}) not found in cfg=f{config}')
        sec = config[msg.repo]

        # Validate HMAC of "message" bytes from the client
        if not msg.verify():
            raise ValueError(f'Invalid signature on {msg.repo}')

        diff = None
        try:
            if sec.getboolean('bare'):
                log.info("Bare repo fetch...")
                update_repo(sec['local'], sec['url'], True, sec.get('owner'))
            else:
                diff = make_repo_state(sec['local'], sec['url'], msg.before, msg.state, sec.get('owner'))
            log.info("GitRepo at %s synced %s --> %s by %s <%s>",
                     sec['local'], msg.before, msg.state, msg.fullname, msg.email)
        except GitExcept as e:
            log.exception("Exception with git: %s", e)
            raise

        postscript = run_postscript_and_notify(msg, sec['local'], sec.get('postscript'), diff)
        reply = f"Repo in {sec['local']} updated to state {msg.state}\n"
        if postscript:
            reply += f"\nPost script {sec.get('postscript')} returns:\n"
        return reply.encode('utf8') + postscript


def make_repo_state(path: str, url: str, oldhash: str, newhash: str, user: Optional[str]) -> str:
    """ Make sure git repo from @url is in state @newhash in folder @path """

    git = update_repo(path, url, False, user)
    current_hash = git.rev_parse('HEAD')
    if oldhash != current_hash:
        log.warning("Repo in unexpected state (%s) != upstream (%s)",
                    current_hash, oldhash)
    git.reset(newhash)

    return git.diff(oldhash, newhash, stat=True)


def update_repo(path: str, url: str, bare: bool, owner: Optional[str]) -> GitRepo:
    """ Run a fetch in the repo given """

    git = GitRepo(path, url, bare, runas=owner)
    git.fetch()
    return git


def run_postscript_and_notify(m: Message, path: str, script: Optional[str], diff: Optional[str]) -> bytes:

    msg = f"""\
Hello,

Git Deploy was done for {m.repo} on {socket.getfqdn()} in {path}
setting state {m.state} for branch {m.branch}.
"""
    if diff:
        msg += '\nChanges:\n\n' + diff + '\n'
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

    # Explicit string server_address
    sa: str = config['DEFAULT']['socket']

    def __init__(self):
        super().__init__(self.sa, SyncRequestHandler)

    def _stat_socket(self) -> Optional[os.stat_result]:
        """ Return socket stat only if it exists, raising error if it exists
            and isn't a socket
        """
        try:
            st = os.stat(self.sa)
        except OSError:
            return None
        if not stat.S_ISSOCK(st.st_mode):
            raise Exception("Address exists and is not a socket")
        return st

    def server_bind(self):
        """ Create a unix socket, mimicing the owner / group / permissions of
            an existing socket if one exists
        """

        st = self._stat_socket()
        if st:
            os.unlink(self.server_address)

        self.socket.bind(self.server_address)

        if st:
            os.chown(self.server_address, st.st_uid, st.st_gid)
        os.chmod(self.server_address, st.st_mode if st else 0o777)

        self.server_address = self.socket.getsockname()


def daemon_main():
    run_serverclass_thread(SyncServer())
