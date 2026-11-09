from django.test import SimpleTestCase

from operations.release_version import ReleaseVersionError, validate_release_tag


class ReleaseVersionTests(SimpleTestCase):
    def test_accepts_valid_semver_tag(self):
        self.assertEqual(validate_release_tag("v1.2.3", ["v1.0.0"]), (1, 2, 3))

    def test_rejects_malformed_or_leading_zero_versions(self):
        for tag in ("1.2.3", "v1.2", "v01.2.3", "v1.2.3-rc.1", "v1.2.3.4"):
            with self.subTest(tag=tag), self.assertRaises(ReleaseVersionError):
                validate_release_tag(tag, ["v1.0.0"])

    def test_rejects_reusing_an_existing_version(self):
        with self.assertRaisesRegex(ReleaseVersionError, "already exists"):
            validate_release_tag("v1.2.3", ["v1.0.0", "v1.2.3"])

    def test_requires_first_production_version_to_be_one_zero_zero(self):
        self.assertEqual(validate_release_tag("v1.0.0", []), (1, 0, 0))
        with self.assertRaisesRegex(ReleaseVersionError, "first production release"):
            validate_release_tag("v0.9.0", [])
