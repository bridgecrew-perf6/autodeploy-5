import logging
import configparser
import os
import sys
import itertools

__all__ = ['config', 'socket_path', 'mail_host', 'daemon_key', 'webd_port']

cfgfile = os.getenv('AUTODEPLOYCFG', '/etc/autodeploy.cfg')

# Emulate a "DEFAULT" section by injecting it before the first line of file

mode = os.stat(cfgfile).st_mode
if mode & 0b110:
    raise Warning('Config file %s is world-readable/writable' % cfgfile)

config = configparser.ConfigParser()
with open(cfgfile, 'r') as fp:
    config.read_file(itertools.chain(['[DEFAULT]'], fp), source=cfgfile)


def setup_logging():
    loglevel = 'debug' if '-d' in sys.argv else config['DEFAULT'].get('loglevel', 'info')
    lvl = getattr(logging, loglevel.upper())

    c = {'level': lvl, 'format': r'%(asctime)-15s %(name)s %(levelname)s %(message)s'}

    loc = config['DEFAULT'].get('loglocation', 'stderr')
    if loc == 'stdout':
        c['stream'] = sys.stdout
    elif loc == 'stderr':
        c['stream'] = sys.stderr
    else:
        c['filename'] = loc
    logging.basicConfig(**c)


socket_path = config['DEFAULT']['socket']
mail_host = config['DEFAULT'].get('smtphost')
daemon_key = config['DEFAULT']['daemonkey']
webd_port = config['DEFAULT'].get('webport')

setup_logging()
