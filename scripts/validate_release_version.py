#!/usr/bin/env python3
"""Validate a release tag and emit normalized version metadata as JSON."""

from __future__ import annotations

import argparse
import json
import sys

from operations.release_version import ReleaseVersionError, validate_release_tag


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--existing-tags", default="")
    args = parser.parse_args()

    existing_tags = [line.strip() for line in args.existing_tags.splitlines() if line.strip()]
    try:
        major, minor, patch = validate_release_tag(args.tag, existing_tags)
    except ReleaseVersionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps({"tag": args.tag, "version": f"{major}.{minor}.{patch}"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
