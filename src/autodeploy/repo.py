# Represent a Git repository checked out on disk with methods to clone/fetch/read
# info about it.

from typing import Optional

import os
import logging

from .util import get_output

log = logging.getLogger(__name__)


class GitExcept(Exception):
    pass


class GitRepo(object):
    """ Represent a git repository as checked out on a server with an optional
        upstream url and possible bare
    """

    def __init__(self, dir: str, remote: Optional[str] = None, bare: bool = False):
        """ Clone the repo in constructor if not exists and @remote is given """

        self.dir = dir
        if remote and not self.exists():
            log.info("Cloning %s into %s", remote, dir)
            parent = os.path.abspath(os.path.join(self.dir, os.pardir))
            ifbare = '--bare ' if bare else ''
            output, rc = get_output('git clone {2}{0} {1}'.format(remote, dir, ifbare),
                                    cwd=parent)
            if rc != 0:
                log.error("Error cloning %s into %s\n%s", remote, parent, output)
                raise GitExcept("Clone error")
        elif bare and self.exists():
            if self.rev_parse('--is-bare-repository') != 'true':
                raise GitExcept('Bare repo at {0} is not actually bare')

    def rev_parse(self, ref: str) -> Optional[str]:
        hash, rc = get_output('git rev-parse {0}'.format(ref), cwd=self.dir)
        return hash.decode('ascii').strip('\n') if rc == 0 else None

    def fetch(self) -> None:
        out, rc = get_output('git fetch', cwd=self.dir)
        log.debug("git fetching in %s", self.dir)
        if rc != 0:
            log.error("Error running git-fetch: %s", out)
            raise GitExcept("Error running git-fetch")

    def exists(self) -> bool:
        return os.path.exists(self.dir)

    def current_ref(self, ref: str ='HEAD') -> Optional[str]:
        out, r = get_output('git symbolic-ref --short -q {0}'.format(ref),
                            cwd=self.dir)
        return out.decode('ascii').strip('\n') if r == 0 else None

    def reset(self, hash: str) -> None:
        out, r = get_output(f'git reset --hard {hash}', cwd=self.dir)
        log.debug("git resetting to %s", hash)
        if r != 0:
            log.error("Error resetting to %s:\n%s", hash, out)
            raise GitExcept("Error git hard-reset")

    def diff(self, first: str, second: str, stat: bool = True) -> str:
        cmd = 'git diff' + ' --stat ' if stat else ' '
        out, r = get_output(f'{cmd} {first} {second}')
        log.debug('%s %s %s', cmd, first, second)
        if r != 0:
            log.error("Error running git diff %s %s!", first, second)
            raise GitExcept('Error git-diff!')
        return out.decode('ascii').strip('\n')
