# Methods so take the webhook output json and turn it into a "message" packet
# and to construct a usefull class from that packet that the daemon can use
#
# Message format:
#        repo-name \\n
#        branch:hashofoldstate:hashofnewstate \\n
#        username:person-name:email \\n
#        signature

from typing import Tuple

from autodeploy import daemon_key

import socket
import hmac


def encode_message(json: dict) -> bytes:
    """ Make a "message packet" (bytes) for transmitting over the wire
        and sign it with the key from the configfile for the daemon
    """
    p = json['pusher']
    n = json['repository']['full_name']
    refstr = f"{json['ref']}:{json['before']}:{json['after']}"
    pusherstr = f"{p['login']}:{p['full_name']}:{p['email']}"
    msg = f'{n}\n{refstr}\n{pusherstr}'
    hm = hmac.new(daemon_key, msg.encode('utf8'), digestmod='sha256')
    return f"{msg}\n{hm.hexdigest()}".encode('utf8')


class Message(object):

    repo:     str   # Repo name from cfg-file and webhook
    branch:   str   # branch to act on if not bare
    before:   str   # state we expect the repo to be in before changing
    state:    str   # new state (hash) after commit is applied
    pusher:   str   # username of who pushed
    fullname: str   # real name of who pushed
    email:    str   # email of who pushed
    digest:   str   # signature digest

    @classmethod
    def from_msg(cls, msg: bytes) -> 'Message':
        c = cls()
        c.repo, ref, person, c.digest = msg.decode('utf8').split('\n')
        c.branch, c.before, c.state = ref.split(':')
        c.pusher, c.fullname, c.email = person.split(':')
        return c

    def verify(self) -> bool:
        """ Verify the signature of this message against the key in the
            config file
        """
        m = f"{self.repo}\n{self.branch}:{self.before}:{self.state}\n"
        m += f"{self.pusher}:{self.fullname}:{self.email}"
        hm = hmac.new(daemon_key, m.encode('utf8'), 'sha256')
        return hmac.compare_digest(hm.hexdigest(), self.digest)


def send_message(msg_bytes: bytes, unixsocket: str) -> Tuple[str, bool]:
    """ Act as a client to the daemon SyncServer, taking an encoded message
        sending it to the daemon at @unixsocket, and returning the answer

        Returns the answer and status from the daemon
    """

    # Connect send and signal we're done with the socket before
    # getting the reply from the daemon
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(unixsocket)

        s.sendall(msg_bytes)
        s.shutdown(socket.SHUT_WR)
        data = b''
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        ans = data.decode('utf8').split('\n')
    return '\n'.join(ans[1:]), ans[0] == 'OK'
