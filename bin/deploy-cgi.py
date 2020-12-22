#!/usr/bin/env python3
import sys
import os
import traceback

from autodeploy import socket_path
from autodeploy.webhook import WebhookOutput
from autodeploy.message import send_message, encode_message

print("Content-type: text/plain")


def err_exit(message: str = 'An error occured', status: int = 400) -> None:
    print(f'Status: {status}\n\n{message}')
    sys.exit(1)


def get_signature():
    try:
        return os.environ['HTTP_X_GITEA_SIGNATURE']
    except KeyError:
        err_exit('No signature header found', 401)


def recieve_and_submit(data, sig):
    data = WebhookOutput(data, sig)
    if not data.validate():
        err_exit('Unknown repo or invalid signature', 403)
    return send_message(encode_message(data.json, data.cfg['secret']), socket_path)


if __name__ == '__main__':
    try:
        out, ok = recieve_and_submit(sys.stdin.read(), get_signature())
    except Exception as e:
        err_exit('CGI Exception occured %s: %s\n%s' %
                 (socket_path, str(e), '\n'.join(traceback.format_tb(e.__traceback__))), 501)

    if not ok:
        err_exit('Error occured processing hook: %s' % out, 500)
    else:
        print(f'Status: 200\n\n{out}')
