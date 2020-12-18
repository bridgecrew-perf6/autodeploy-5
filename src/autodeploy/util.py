from typing import Tuple
import subprocess

import smtplib

from email.message import EmailMessage



def get_output(cmd: str, cwd: str='') -> Tuple[bytes, int]:
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return p.stdout, p.returncode


def send_email(to: str, sub: str, message: str, sender: str='Deploy Daemon <root@localhost>'):
    msg = EmailMessage()
    msg.set_content(message)
    msg['Subject'] = sub
    msg['From'] = sender
    msg['To'] = to

    s = smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()
