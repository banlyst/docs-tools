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

import hashlib
import os
import shutil
import tarfile
import logging
import contextlib

logger = logging.getLogger('giza.files')

class FileNotFoundError(Exception):
    pass

class InvalidFile(Exception):
    pass

class FileOperationError(Exception):
    pass

@contextlib.contextmanager
def cd(path):
    cur_dir = os.getcwd()

    os.chdir(path)

    yield

    os.chdir(cur_dir)

class FileLogger(object):
    def __init__(self, logger, level=logging.INFO):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message != '\n':
            self.logger.log(self.level, message)

def safe_create_directory(path):
    try:
        os.makedirs(path)
        return True
    except OSError as e:
        if os.path.isdir(path):
            return None
        elif os.path.isfie(path):
            logger.error('{0} is a file not a directory.'.format(e))
            raise e
        else:
            logger.error('encountered error creating directory: ' + path)
            raise e

def verbose_remove(path):
    if os.path.exists(path):
        logger.info('clean: removing {0}'.format(path))
        os.remove(path)

def rm_rf(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)

def tarball(name, path, newp=None, cdir=None):
    tarball_path = os.path.dirname(name)
    safe_create_directory(tarball_path)

    logger.debug('creating tarball: {0}'.format(name))
    with tarfile.open(name, 'w:gz') as t:
        if newp is not None:
            arcname = os.path.join(newp, os.path.basename(path))
        else:
            arcname = None

        if cdir is not None:
            path = os.path.join(cdir, path)

        logger.debug('tarball internal path {0}'.format(path))

        t.add(name=path, arcname=arcname)

    logger.info('created tarball: {0}'.format(name))

def symlink(name, target):
    if not os.path.islink(name):
        try:
            os.symlink(target, name)
        except AttributeError:
            from win32file import CreateSymbolicLink
            CreateSymbolicLink(name, target)
        except ImportError:
            logger.error("platform does not contain support for symlinks. Windows users need to pywin32.")
            exit(1)

def expand_tree(path, input_extension='yaml'):
    file_list = []

    for root, sub_folders, files in os.walk(path):
        for file in files:
            if file.startswith('.#'):
                continue
            elif file.endswith('swp'):
                continue
            else:
                f = os.path.join(root, file)
                if input_extension != None:
                    if isinstance(input_extension, list):
                        if os.path.splitext(f)[1][1:] not in input_extension:
                            continue
                    else:
                        if not f.endswith(input_extension):
                            continue

                file_list.append(f)

    return file_list

def md5_file(file, block_size=2**20):
    md5 = hashlib.md5()

    with open(file, 'rb') as f:
        for chunk in iter(lambda: f.read(128*md5.block_size), b''):
            md5.update(chunk)

    return md5.hexdigest()

def copy_always(source_file, target_file, name='build'):
    if os.path.isfile(source_file) is False:
        msg = "{0}: Input file '{1}' does not exist.".format(name, source_file)
        logger.critical(msg)
        raise FileOperationError(msg)
    else:
        safe_create_directory(os.path.dirname(target_file))
        shutil.copyfile(source_file, target_file)

    logger.debug('{0}: copied {1} to {2}'.format(name, source_file, target_file))

def copy_if_needed(source_file, target_file, name='build'):
    if os.path.isfile(source_file) is False or os.path.isdir(source_file):
        msg = "{0}: Input file '{1}' does not exist.".format(name, source_file)
        logger.critical(msg)
        raise FileOperationError(msg)
    elif os.path.isfile(target_file) is False:
        safe_create_directory(os.path.dirname(target_file))
        shutil.copyfile(source_file, target_file)

        if name is not None:
            logger.debug('{0}: created "{1}" which did not exist.'.format(name, target_file))
    else:
        if md5_file(source_file) == md5_file(target_file):
            if name is not None:
                logger.debug('{0}: "{1}" not changed.'.format(name, source_file))
        else:
            shutil.copyfile(source_file, target_file)

            if name is not None:
                logger.debug('{0}: "{1}" changed. Updated: {2}'.format(name, source_file, target_file))

def create_link(input_fn, output_fn):
    out_dirname = os.path.dirname(output_fn)

    if out_dirname != '':
        safe_create_directory(out_dirname)

    if os.path.islink(output_fn):
        os.remove(output_fn)
    elif os.path.isdir(output_fn):
        msg = "link: {1} exists and is a directory".format(output_fn)
        logger.critical(msg)
        raise FileOperationError(msg)
    elif os.path.exists(output_fn):
        msg = 'could not create a symlink at {1}.'.format('link', output_fn)
        logger.critical(msg)
        raise FileOperationError(msg)
    out_base = os.path.basename(output_fn)
    if out_base == "":
        msg = 'could not create a symlink at {1}.'.format('link', output_fn)
        logger.critical(msg)
        raise FileOperationError(msg)
    else:
        symlink(out_base, input_fn)
        os.rename(out_base, output_fn)
        logger.debug('{0} created symbolic link pointing to "{1}" named "{2}"'.format('symlink', input_fn, out_base))

def decode_lines_from_file(fn):
    with open(fn, 'r') as f:
        return [ line.decode('utf-8').rstrip() for line in f.readlines() ]

def encode_lines_to_file(fn, lines):
    with open(fn, 'w') as f:
        f.write('\n'.join(lines).encode('utf-8'))
        f.write('\n')
