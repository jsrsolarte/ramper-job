"""Validate that a main commit is the merge of the approved staging PR."""
import json
import re
import sys
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def is_sha(value: Any) -> bool:
    return isinstance(value, str) and SHA_RE.fullmatch(value) is not None


def merged_staging_pr_head(pull_requests: list[dict[str, Any]], release_sha: str) -> str:
    """Return the unique merged staging PR head for release_sha, or reject it."""
    if not is_sha(release_sha):
        raise ValueError("Release SHA must be a full lowercase Git SHA")
    if not isinstance(pull_requests, list) or any(not isinstance(pr, dict) for pr in pull_requests):
        raise ValueError("GitHub PR response must be a JSON array of pull requests")

    matches = [
        pr for pr in pull_requests
        if pr.get("merged_at")
        and pr.get("merge_commit_sha") == release_sha
        and pr.get("base", {}).get("ref") == "main"
        and pr.get("head", {}).get("ref") == "staging"
    ]
    if len(matches) != 1:
        raise ValueError("Commit is not the unique merge of a staging PR into main")

    head_sha = matches[0].get("head", {}).get("sha")
    if not is_sha(head_sha):
        raise ValueError("Merged staging PR has an invalid head SHA")
    return head_sha


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] != "pr-head":
        print("Usage: check_production_promotion.py pr-head <release-sha>", file=sys.stderr)
        return 2
    try:
        pull_requests = json.load(sys.stdin)
        print(merged_staging_pr_head(pull_requests, argv[2]))
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
