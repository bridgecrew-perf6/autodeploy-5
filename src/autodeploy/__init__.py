import logging
import configparser
import os
import sys
import itertools

__all__ = ['config', 'socket_path']

cfgfile = os.getenv('AUTODEPLOYCFG', '/etc/autodeploy.cfg')

# Emulate a "DEFAULT" section by injecting it before the first line of file
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

setup_logging()
