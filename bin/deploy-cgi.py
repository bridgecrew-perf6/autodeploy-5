#!/usr/bin/env python3
import sys
import os

from autodeploy.webhook import WebhookOutput

print("Content-type: text/plain")


def err_exit(message: str = 'An error occured', status: int = 400) -> None:
    print(f'\nStatus: {status}\n\n{message}')
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
    return data.notify_daemon()


if __name__ == '__main__':
    try:
        out, rc = recieve_and_submit(sys.stdin.read(), get_signature())
    except Exception as e:
        err_exit('CGI Exception occured: %s' % e, 500)
