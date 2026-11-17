"""Reject stale staging candidates; allow only verified pin-only bot commits after them."""
import argparse
import subprocess
import sys

PIN_PATH = "deploy/overlays/staging/kustomization.yaml"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def candidate_is_current(candidate, head):
    if subprocess.run(["git", "merge-base", "--is-ancestor", candidate, head],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
        return False
    candidate = git("rev-parse", "--verify", candidate + "^{commit}")
    current = git("rev-parse", "--verify", head + "^{commit}")
    while current != candidate:
        parents = git("rev-list", "--parents", "-n", "1", current).split()
        if len(parents) != 2:
            return False
        if git("show", "-s", "--format=%ae", current) != BOT_EMAIL:
            return False
        if not git("show", "-s", "--format=%s", current).startswith("deploy(staging): "):
            return False
        if git("diff", "--name-only", parents[1], current).splitlines() != [PIN_PATH]:
            return False
        current = parents[1]
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate")
    parser.add_argument("head")
    args = parser.parse_args()
    try:
        valid = candidate_is_current(args.candidate, args.head)
    except subprocess.CalledProcessError:
        valid = False
    print("current" if valid else "stale or ambiguous")
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
