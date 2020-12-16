#!/usr/bin/python3

import os
import sys
import json
import hmac
import redis
import hashlib

data = sys.stdin.read()

# HMAC signing key, set in gitea
SECRET = 'y8NMQz1f5uZrZcJ3'

print("Content-type: text/plain")


def verify():
    hm = hmac.new(SECRET, digestmod=hashlib.sha256)

    hm.update(data)
    sig = os.environ.get('HTTP_X_GITEA_SIGNATURE', '')
    if hm.hexdigest() != sig:
        print("Status: 400")
        print("\nBad Digest: {} != {}".format(hm.hexdigest(), sig))
        sys.exit(1)


def getjson():
    try:
        return json.loads(data)
    except ValueError:
        print("Status: 400")
        print("\nBad JSON detected!")
        sys.exit(1)


def main(branch):
    verify()
    j = getjson()
    ref = j['ref']
    if ref != "refs/heads/" + branch:
        print("Status: 400\n\nWrong branch pushed")
        sys.exit(1)

    r = redis.StrictRedis()
    r.lpush('kti', '{0}:{1}:{2}'.format(ref, j['before'], j['after']))
    r.set(j['after'], j['pusher']['email'], ex=60)


if __name__ == '__main__':
    try:
        main('master')
    except Exception as e:
        print("Status: 400")
        print("\nException occured: %s" % e)
        sys.exit(1)
    print("\nOk")
