import os

from . import log
from .util import get_output


class GitExcept(Exception):
    pass


class GitRepo(object):

    def __init__(self, dir, remote=None):
        self.dir = dir
        if remote and not self.exists():
            log.info("Cloning %s into %s", remote, dir)
            parent = os.path.abspath(os.path.join(self.dir, os.pardir))
            output, rc = get_output('git clone {0} {1}'.format(remote, dir),
                                    cwd=parent)
            if rc != 0:
                log.error("Error cloning %s into %s\n%s", remote, parent, output)
                raise GitExcept("Clone error")

    def current_state(self, ref):
        hash, rc = get_output('git rev-parse {0}'.format(ref), cwd=self.dir)
        return hash if rc == 0 else None

    def fetch(self):
        out, rc = get_output('git fetch', cwd=self.dir)
        if rc != 0:
            log.error("Error running git-fetch: %s", out)
            raise GitExcept("Error running git-fetch")

    def exists(self):
        return os.path.exists(self.dir)

    def current_ref(self, ref='HEAD'):
        out, r = get_output('git symbolic-ref --short -q {0}'.format(ref),
                            cwd=self.dir)
        return out if r == 0 else None

    def reset(self, hash):
        out, r = get_output(f'git reset --hard {hash}', cwd=self.dir)
        if r != 0:
            log.error("Error resetting to %s:\n%s", hash, out)
            raise GitExcept("Error git hard-reset")

