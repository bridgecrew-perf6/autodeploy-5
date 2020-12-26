#!/usr/bin/env python3
import sys
import os
import traceback

from autodeploy.webhook import check_webhook_output
from autodeploy.message import Message, send_message

print("Content-type: text/plain")


def err_exit(message: str = 'An error occured', status: int = 400) -> None:
    print(f'Status: {status}\n\n{message}')
    sys.exit(1)


def get_signature():
    try:
        return os.environ['HTTP_X_GITEA_SIGNATURE']
    except KeyError:
        err_exit('No signature header found', 401)


def recieve_and_submit(rawjson, sig):

    if not check_webhook_output(rawjson, sig):
        err_exit('Invalid signature, repo, or branch', 403)
        return
    return send_message(Message.from_json(rawjson).as_bytes())


if __name__ == '__main__':
    try:
        out, ok = recieve_and_submit(sys.stdin.read(), get_signature())
    except Exception as e:
        err_exit('CGI Exception occured: %s\n%s' %
                 (str(e), '\n'.join(traceback.format_tb(e.__traceback__))), 501)

    if not ok:
        err_exit('Error occured processing hook: %s' % out, 500)
    else:
        print(f'Status: 200\n\n{out}')
