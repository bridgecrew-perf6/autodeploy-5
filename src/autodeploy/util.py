from typing import Tuple, List
import subprocess
import signal
import threading
import shlex
import enum

import smtplib

from email.message import EmailMessage

from autodeploy import mail_host

import logging

log = logging.getLogger(__name__)


def get_output(cmd: str, cwd: str = '.') -> Tuple[bytes, int]:
    args = shlex.split(cmd)
    log.debug("Running %s (in %s)", args, cwd)
    p = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return p.stdout, p.returncode


def send_email(to: str, sub: str, message: str, sender: str = 'Deploy Daemon <root@localhost>'):
    msg = EmailMessage()
    msg.set_content(message)
    msg['Subject'] = sub
    msg['From'] = sender
    msg['To'] = to

    s = smtplib.SMTP(mail_host)
    s.send_message(msg)
    s.quit()


class StopServer(Exception):
    pass


def run_serverclass_thread(srv, stopsigs: List[enum.IntEnum] = [signal.SIGTERM, signal.SIGINT]):
    """ Run a server in another thread while pause() in current thread to
        handle signals to request a clean shutdown
    """
    def sighandle(signal, frame):
        raise StopServer()

    for sig in stopsigs:
        signal.signal(sig, sighandle)

    srv_thread = threading.Thread(target=srv.serve_forever)
    srv_thread.start()
    while True:
        try:
            signal.pause()
        except StopServer:
            srv.shutdown()
            break
    srv_thread.join()
