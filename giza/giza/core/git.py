# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Provides the :class:`~giza.git.GitRepo()` class that provides a thin
Python-layer on top of common git operations.
"""

import logging
import os
import re
from contextlib import contextmanager

from giza.tools.command import command, CommandError

logger = logging.getLogger('giza.core.git')

class GitError(Exception): pass

class GitRepo(object):
    """
    An object that represents a git repository, and provides methods to wrap
    many common git commands and basic aggregate operations.
    """

    def __init__(self, path=None):
        """
        :param string path: Optional. Defines a the path of the git
           repository. If not specified, defaults to the current working
           directory.
        """

        if path is None:
            self.path = os.getcwd()
        else:
            self.path = path

        logger.debug("created git repository management object for {0}".format(self.path))

    def cmd(self, *args):
        args = ' '.join(args)

        try:
            return command(command='cd {0} ; git {1}'.format(self.path, args), capture=True)
        except CommandError as e:
            raise GitError(e)

    def remotes(self):
        return self.cmd('remote').out.split('\n')

    def author_email(self, sha=None):
        if sha is None:
            sha = self.sha()

        return self.cmd('log', sha + '~..' + sha, "--pretty='format:%ae'").out

    def branch_exists(self, name):
        r = self.cmd('branch --list ' + name).out.split('\n')
        if '' in r:
            r.remove('')

        if name in r:
            return True
        else:
            return False

    def branch_file(self, path, branch='master'):
        return self.cmd('show {branch}:{path}'.format(branch=branch, path=path)).out

    def checkout(self, ref):
        self.cmd('checkout', ref)
        return True

    def create_branch(self, name, tracking=None):
        args = ['branch', name]

        if tracking is not None:
            args.append(tracking)

        return self.cmd(*args)

    def checkout_branch(self, name, tracking=None):
        if self.current_branch() == name:
            return

        args = ['checkout']

        if not self.branch_exists(name):
            args.append('-b')

        args.append(name)

        if tracking is not None:
            args.append(tracking)

        return self.cmd(*args)

    def remove_branch(self, name, force=False):
        args = ['branch']

        if force is False:
            args.append('-d')
        else:
            args.append('-D')

        args.append(name)

        return self.cmd(*args)

    def rebase(self, onto):
        return self.cmd('rebase', onto)

    def merge(self, branch):
        return self.cmd('merge', branch)

    def hard_reset(self, ref='HEAD'):
        return self.cmd('reset', '--hard', ref)

    def reset(self, ref='HEAD'):
        return self.cmd('reset', ref)

    def fetch(self, remote='origin'):
        return self.cmd('fetch', remote)

    def update(self):
        return self.cmd('pull', '--rebase')

    def pull(self, remote='origin', branch='master'):
        return self.cmd('pull', remote, branch)

    def current_branch(self):
        return self.cmd('symbolic-ref', 'HEAD').out.split('/')[2]

    def sha(self, ref='HEAD'):
        return self.cmd('rev-parse', '--verify', ref).out

    def clone(self, remote, repo_path=None, branch=None):
        args = ['clone', remote]

        if branch is not None:
            args.extend(['--branch', branch])

        if repo_path is not None:
            args.append(repo_path)

        return self.cmd(*args)

    def commit_messages(self, num=1):
        args = ['log', '--oneline', '--max-count=' + str(num) ]
        log = self.cmd(*args)

        return [ ' '.join(m.split(' ')[1:])
                 for m in log.out.split('\n') ]

    def cherry_pick(self, *args):
        if len(args) == 1:
            args = args[0]

        for commit in args:
            self.cmd('cherry-pick', commit)
            logger.info('cherry picked ' + commit )

    def am(self, patches, repo=None, sign=False):
        cmd_base = 'curl {path} | git am --3way'

        if sign is True:
            cmd_base += ' --signoff'

        for obj in patches:
            if obj.startswith('http'):
                if not obj.endswith('.patch'):
                    obj += '.patch'

                command(cmd_base.format(path=obj))
                logger.info("applied {0}".format(obj))
            elif re.search('[a-zA-Z]+', obj):
                path = '/'.join([ repo, 'commit', obj ]) + '.patch'

                command(cmd_base.format(path=path))
                logger.info('merged commit {0} for {1} into {2}'.format(obj, repo, self.current_branch()))
            else:
                if repo is None:
                    logger.warning('not applying "{0}", because of missing repo'.format(obj))
                else:
                    path = '/'.join([ repo, 'pull', obj ]) + '.patch'
                    command(cmd_base.format(path=path))
                    logger.info("applied {0}".format(obj))

    @contextmanager
    def branch(self, name):
        starting_branch = self.current_branch()

        if name != starting_branch:
            self.checkout(name)

        yield

        if name != starting_branch:
            self.checkout(starting_branch)
