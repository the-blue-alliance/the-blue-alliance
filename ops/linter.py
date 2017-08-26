#!/usr/bin/python

"""
Based on https://github.com/cbrueffer/pep8-git-hook
Forked from https://gist.github.com/810399
"""
from __future__ import with_statement
import os
import re
import shutil
import subprocess
import sys
import tempfile
import argparse

# don't fill in both of these
select_codes = ["E111", "E125", "E203", "E261", "E262", "E301", "E302", "E303",
                "E502", "E701", "W291", "W293"]
ignore_codes = []


def system(*args, **kwargs):
    kwargs.setdefault('stdout', subprocess.PIPE)
    proc = subprocess.Popen(args, **kwargs)
    out, err = proc.communicate()
    return out


def get_modified_files():
    modified = re.compile('^[AM]+\s+(?P<name>.*\.py)', re.MULTILINE)
    files = system('git', 'status', '--porcelain')
    return modified.findall(files)


def get_files_for_commit(commit_sha):
    modified = re.compile('^(?P<name>.*\.py)', re.MULTILINE)
    files = system('git', 'diff', '--diff-filter=AMR', '--name-only', commit_sha)
    return modified.findall(files)


def get_files_since_branch(branch):
    modified = re.compile('^(?P<name>.*\.py)', re.MULTILINE)
    files = system('git', 'diff', '--diff-filter=AMR', '--name-only', branch, "HEAD")
    return modified.findall(files)


def main():
    parser = argparse.ArgumentParser(description="Lint some files")
    parser.add_argument('--commit', help="Commit has to lint")
    parser.add_argument('--base', help="Lint changes between now and the base branch")
    args = parser.parse_args()

    if args.commit:
        files = get_files_for_commit(args.commit)
    elif args.base:
        files = get_files_since_branch(args.base)
    else:
        files = get_modified_files()

    print "Linting: {}".format(files)
    tempdir = tempfile.mkdtemp()
    for name in files:
        filename = os.path.join(tempdir, name)
        filepath = os.path.dirname(filename)

        if not os.path.exists(filepath):
            os.makedirs(filepath)
        with file(filename, 'w') as f:
            system('git', 'show', ':' + name, stdout=f)

    try:
        if select_codes and ignore_codes:
            print "Error: select and ignore codes are mutually exclusive"
            sys.exit(1)
        elif select_codes:
            output = system('pep8', '--select', ','.join(select_codes), '.', cwd=tempdir)
        elif ignore_codes:
            output = system('pep8', '--ignore', ','.join(ignore_codes), '.', cwd=tempdir)
        else:
            output = system('pep8', '.', cwd=tempdir)
    except OSError:
        print "ERROR: PEP8 needs to be installed!"
        print "You can install it by running: easy_install pep8"
        sys.exit(1)

    shutil.rmtree(tempdir)
    if output:
        print 'PEP8 style violations have been detected.  Please fix them\n' \
              'or force the commit with "git commit --no-verify".\n'
        print output,
        sys.exit(1)


if __name__ == '__main__':
    main()
