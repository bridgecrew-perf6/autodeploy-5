import logging
import os

__all__ = ['log', 'config']

logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s %(level)s %(message)s')
log = logging.getLogger('')

config = os.getenv('AUTODEPLOYCFG', '/etc/autodeploy.cfg')
