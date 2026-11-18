"""Update the production image pin only for the validated current candidate."""
import re
import sys
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PIN_RE = re.compile(r"(?m)^(\s*)(?:digest:\s*sha256:[0-9a-f]{64}|newTag:\s*[^\s#]+)\s*$")


def update_pin(
    path: Path,
    image_sha: str,
    release_sha: str,
    current_main_sha: str,
    current_staging_sha: str,
) -> None:
    """Verify live refs before changing the one production image pin."""
    shas = (image_sha, release_sha, current_main_sha, current_staging_sha)
    if not all(SHA_RE.fullmatch(value or "") for value in shas):
        raise ValueError("All release and candidate refs must be full lowercase Git SHAs")
    if current_main_sha != release_sha:
        raise ValueError("main advanced after the release workflow started")
    if current_staging_sha != image_sha:
        raise ValueError("staging candidate changed after it was validated")

    content = path.read_text(encoding="utf-8")
    updated, replacements = PIN_RE.subn(lambda match: f"{match.group(1)}newTag: {image_sha}", content)
    if replacements != 1:
        raise ValueError(f"Expected one production image pin, found {replacements}")
    path.write_text(updated, encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) != 6:
        print(
            "Usage: update_production_pin.py <overlay> <image-sha> <release-sha> "
            "<current-main-sha> <current-staging-sha>",
            file=sys.stderr,
        )
        return 2
    try:
        update_pin(Path(argv[1]), *argv[2:])
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
