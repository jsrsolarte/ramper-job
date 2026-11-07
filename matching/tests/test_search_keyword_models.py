from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from matching.models import MatchingConfig, ProfileSearchTerms
from matching.services import get_profile_search_terms
from profiles.models import Profile, ProfileRevision


class ProfileSearchTermsModelTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("member")
        profile = Profile.objects.create(owner=user, cv_file="profiles/1/cv/v1.pdf", revision_number=1)
        self.revision = ProfileRevision.objects.create(
            profile=profile,
            version=1,
            search_phrases=["Analista de procesos"],
            cv_file_path=profile.cv_file.name,
        )
        self.config = MatchingConfig.objects.create(
            version=1,
            search_prompt="Busca roles respaldados por el perfil",
            analysis_prompt="Analiza",
            organization_prompt="Organiza",
        )

    def test_terms_are_unique_per_profile_revision_and_config(self):
        ProfileSearchTerms.objects.create(
            profile_revision=self.revision,
            matching_config=self.config,
            keywords=["procesos", "analista de procesos"],
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            ProfileSearchTerms.objects.create(
                profile_revision=self.revision,
                matching_config=self.config,
                keywords=["duplicado"],
            )

        self.assertEqual(self.revision.search_term_sets.get().keywords, ["procesos", "analista de procesos"])

    def test_revision_history_can_keep_distinct_search_term_sets(self):
        first = ProfileSearchTerms.objects.create(
            profile_revision=self.revision,
            matching_config=self.config,
            keywords=["procesos"],
        )
        second_config = MatchingConfig.objects.create(
            version=2,
            search_prompt="Busca cargos y habilidades",
            analysis_prompt="Analiza",
            organization_prompt="Organiza",
            is_active=False,
        )
        second = ProfileSearchTerms.objects.create(
            profile_revision=self.revision,
            matching_config=second_config,
            keywords=["mejora continua"],
        )

        self.assertEqual(first.keywords, ["procesos"])
        self.assertEqual(second.keywords, ["mejora continua"])
        self.assertEqual(ProfileRevision.objects.count(), 1)

    @patch("matching.services.extract_revision_text", return_value="CV de procesos")
    @patch("matching.services.request_model_keywords", return_value={"keywords": ["procesos"]})
    def test_existing_terms_are_reused_for_same_revision_and_config(self, request, extract):
        first = get_profile_search_terms(self.revision, self.config)
        second = get_profile_search_terms(self.revision, self.config)

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(ProfileSearchTerms.objects.count(), 1)
        request.assert_called_once()
        extract.assert_called_once_with(self.revision)

    @patch("matching.services.extract_revision_text", return_value="CV actualizado")
    @patch("matching.services.request_model_keywords", return_value={"keywords": ["procesos"]})
    def test_new_profile_revision_or_config_generates_a_new_set(self, request, extract):
        get_profile_search_terms(self.revision, self.config)
        updated_revision = ProfileRevision.objects.create(
            profile=self.revision.profile,
            version=2,
            search_phrases=["Especialista en mejora continua"],
            cv_file_path=self.revision.cv_file_path,
        )
        updated_config = MatchingConfig.objects.create(
            version=2,
            search_prompt="Prompt actualizado",
            analysis_prompt="Analiza",
            organization_prompt="Organiza",
            is_active=False,
        )

        get_profile_search_terms(updated_revision, self.config)
        get_profile_search_terms(updated_revision, updated_config)

        self.assertEqual(ProfileSearchTerms.objects.count(), 3)
        self.assertEqual(request.call_count, 3)
