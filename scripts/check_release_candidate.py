"""Verify a release commit contains precisely the tested application code."""
import subprocess
import sys


def check(candidate, release, staging, main):
    def succeeds(*args):
        return subprocess.run(['git', *args], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode == 0
    return (succeeds('merge-base', '--is-ancestor', release, main)
            and succeeds('merge-base', '--is-ancestor', candidate, staging)
            and succeeds('merge-base', '--is-ancestor', candidate, release)
            and succeeds('diff', '--quiet', candidate, release, '--', '.',
                         ':(exclude).github/**', ':(exclude)openspec/**', ':(exclude)deploy/**'))


if __name__ == '__main__':
    if len(sys.argv) != 5:
        raise SystemExit('Expected candidate, release, staging and main refs')
    raise SystemExit(0 if check(*sys.argv[1:]) else 1)
