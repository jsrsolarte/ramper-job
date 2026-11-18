from pathlib import Path
import tempfile
import unittest

from scripts.check_production_promotion import merged_staging_pr_head
from scripts.update_production_pin import update_pin

RELEASE = "1" * 40
PR_HEAD = "2" * 40
OTHER_HEAD = "3" * 40
STAGING_CANDIDATE = "4" * 40


def pull_request(**overrides):
    pr = {
        "merged_at": "2026-11-18T00:00:00Z",
        "merge_commit_sha": RELEASE,
        "base": {"ref": "main"},
        "head": {"ref": "staging", "sha": PR_HEAD},
    }
    for key, value in overrides.items():
        pr[key] = value
    return pr


class MergedStagingPullRequestTests(unittest.TestCase):
    def test_accepts_unique_merged_staging_pr(self):
        self.assertEqual(merged_staging_pr_head([pull_request()], RELEASE), PR_HEAD)

    def test_rejects_direct_push_without_associated_pull_request(self):
        with self.assertRaisesRegex(ValueError, "unique merge"):
            merged_staging_pr_head([], RELEASE)

    def test_rejects_pull_request_from_another_branch(self):
        pr = pull_request(head={"ref": "feature", "sha": OTHER_HEAD})
        with self.assertRaisesRegex(ValueError, "unique merge"):
            merged_staging_pr_head([pr], RELEASE)

    def test_rejects_pull_request_to_another_base(self):
        pr = pull_request(base={"ref": "release"})
        with self.assertRaisesRegex(ValueError, "unique merge"):
            merged_staging_pr_head([pr], RELEASE)

    def test_rejects_unmerged_or_wrong_commit_pull_request(self):
        for pr in (
            pull_request(merged_at=None),
            pull_request(merge_commit_sha=OTHER_HEAD),
            pull_request(head={"ref": "staging", "sha": "bad-sha"}),
        ):
            with self.subTest(pr=pr), self.assertRaises(ValueError):
                merged_staging_pr_head([pr], RELEASE)

    def test_rejects_ambiguous_multiple_pull_requests(self):
        with self.assertRaisesRegex(ValueError, "unique merge"):
            merged_staging_pr_head([pull_request(), pull_request()], RELEASE)

    def test_rejects_invalid_release_sha(self):
        with self.assertRaisesRegex(ValueError, "full lowercase Git SHA"):
            merged_staging_pr_head([pull_request()], "bad-sha")

    def test_rejects_invalid_api_response_shape(self):
        with self.assertRaisesRegex(ValueError, "JSON array"):
            merged_staging_pr_head({"message": "API unavailable"}, RELEASE)


class ProductionPinGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "kustomization.yaml"
        self.original = "images:\n  - name: app\n    newTag: old\n"
        self.path.write_text(self.original, encoding="utf-8")

    def test_updates_pin_when_main_and_staging_still_match(self):
        update_pin(self.path, STAGING_CANDIDATE, RELEASE, RELEASE, STAGING_CANDIDATE)
        self.assertIn(f"newTag: {STAGING_CANDIDATE}", self.path.read_text(encoding="utf-8"))

    def test_does_not_update_pin_when_main_advanced(self):
        with self.assertRaisesRegex(ValueError, "main advanced"):
            update_pin(self.path, STAGING_CANDIDATE, RELEASE, OTHER_HEAD, STAGING_CANDIDATE)
        self.assertEqual(self.path.read_text(encoding="utf-8"), self.original)

    def test_does_not_update_pin_when_staging_candidate_advanced(self):
        with self.assertRaisesRegex(ValueError, "staging candidate changed"):
            update_pin(self.path, STAGING_CANDIDATE, RELEASE, RELEASE, OTHER_HEAD)
        self.assertEqual(self.path.read_text(encoding="utf-8"), self.original)

    def test_does_not_update_pin_for_invalid_sha_or_ambiguous_overlay(self):
        with self.assertRaisesRegex(ValueError, "full lowercase Git SHAs"):
            update_pin(self.path, "missing-image", RELEASE, RELEASE, STAGING_CANDIDATE)
        self.assertEqual(self.path.read_text(encoding="utf-8"), self.original)

        self.path.write_text(self.original + "  - name: another\n    newTag: old\n", encoding="utf-8")
        malformed = self.path.read_text(encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Expected one production image pin"):
            update_pin(self.path, STAGING_CANDIDATE, RELEASE, RELEASE, STAGING_CANDIDATE)
        self.assertEqual(self.path.read_text(encoding="utf-8"), malformed)

    def test_workflow_checks_image_before_writing_pin_and_fails_closed(self):
        workflow = (Path(__file__).parents[1] / ".github/workflows/production.yml").read_text(
            encoding="utf-8"
        )
        pull_request_check = workflow.index("check_production_promotion.py pr-head")
        image_check = workflow.index("- name: Verify the immutable staging image is available")
        pin_write = workflow.index("- name: Point production at the same tested image")
        commit = workflow.index("- name: Commit and push the production image pin")
        self.assertLess(pull_request_check, image_check)
        self.assertLess(image_check, pin_write)
        self.assertLess(pin_write, commit)
        self.assertNotIn("continue-on-error:", workflow)
        self.assertNotIn("if: always()", workflow)


if __name__ == "__main__":
    unittest.main()
