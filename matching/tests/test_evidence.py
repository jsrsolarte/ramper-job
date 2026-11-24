from io import BytesIO
import json
import math
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase, override_settings
from docx import Document
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from matching.client import ModelCallResult, OmniRouteError
from matching.evidence import ensure_profile_artifacts, select_evidence_for_vacancy, validate_profile_artifacts
from matching.models import MatchingConfig, ProfileEvidence, ProfileSearchTerms
from matching.schemas import InvalidSearchKeywordsError
from profiles.models import Profile, ProfileRevision


class ProfileEvidenceModelTests(TestCase):
    def setUp(self):
        first_user = get_user_model().objects.create_user("first")
        second_user = get_user_model().objects.create_user("second")
        first_profile = Profile.objects.create(owner=first_user)
        second_profile = Profile.objects.create(owner=second_user)
        self.first_revision = ProfileRevision.objects.create(
            profile=first_profile, version=1, cv_file_path="profiles/1/cv/v1.pdf",
        )
        self.second_revision = ProfileRevision.objects.create(
            profile=second_profile, version=1, cv_file_path="profiles/2/cv/v1.pdf",
        )

    def test_evidence_is_unique_per_revision_and_extractor_version(self):
        first = ProfileEvidence.objects.create(
            profile_revision=self.first_revision,
            extractor_version=1,
            source_sha256="a" * 64,
            facts=[{"category": "skill", "source_excerpt": "SQL"}],
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            ProfileEvidence.objects.create(
                profile_revision=self.first_revision,
                extractor_version=1,
                source_sha256="b" * 64,
                facts=[],
            )

        self.assertEqual(self.first_revision.evidence_records.get().pk, first.pk)

    def test_evidence_isolated_by_profile_revision_and_traced_to_source(self):
        first = ProfileEvidence.objects.create(
            profile_revision=self.first_revision,
            extractor_version=1,
            source_sha256="a" * 64,
            facts=[{"category": "skill", "source_excerpt": "Desarrollé informes con SQL."}],
        )
        second = ProfileEvidence.objects.create(
            profile_revision=self.second_revision,
            extractor_version=1,
            source_sha256="b" * 64,
            facts=[{"category": "skill", "source_excerpt": "Administré inventarios."}],
        )

        self.assertEqual(first.profile_revision.profile_id, self.first_revision.profile_id)
        self.assertEqual(second.profile_revision.profile_id, self.second_revision.profile_id)
        self.assertEqual(self.first_revision.evidence_records.get().facts[0]["source_excerpt"], "Desarrollé informes con SQL.")
        self.assertEqual(self.second_revision.evidence_records.get().facts[0]["source_excerpt"], "Administré inventarios.")
        self.assertNotEqual(first.source_sha256, second.source_sha256)


class VacancyEvidenceSelectionTests(SimpleTestCase):
    def setUp(self):
        self.facts = [
            {
                "id": "f1", "category": "experience",
                "statement": "Lideró proyectos de analítica durante 4 años.",
                "source_excerpt": "Lideré proyectos de analítica durante 4 años.",
                "normalized_terms": ["analitica", "proyectos"], "period": "4 años", "metrics": "",
            },
            {
                "id": "f2", "category": "education",
                "statement": "Profesional en Ingeniería de Sistemas.",
                "source_excerpt": "Profesional en Ingeniería de Sistemas, 2018.",
                "normalized_terms": ["ingenieria de sistemas"], "period": "2018", "metrics": "",
            },
            {
                "id": "f3", "category": "certification",
                "statement": "No cuenta con licencia C2.",
                "source_excerpt": "No cuento con licencia C2.",
                "normalized_terms": ["licencia", "c2"], "period": "", "metrics": "",
            },
            {
                "id": "f4", "category": "skill",
                "statement": "Automatizó reportes financieros con SQL.",
                "source_excerpt": "Automaticé reportes financieros con SQL.",
                "normalized_terms": ["sql", "reportes"], "period": "", "metrics": "",
            },
        ]

    def test_matches_normalized_terms_and_reads_nested_mandatory_requirements(self):
        selected = select_evidence_for_vacancy(
            self.facts,
            {
                "title": "Analista de analitica",
                "details": {
                    "requirements": ["Profesional en ingeniería de sistemas", "Licencia C2 obligatoria"],
                    "responsibilities": ["Liderar proyectos de analítica"],
                },
            },
            search_phrases=["Analista de datos"],
        )

        selected_ids = {fact["id"] for fact in selected}
        self.assertTrue({"f1", "f2", "f3"}.issubset(selected_ids))
        self.assertIn("education", next(f for f in selected if f["id"] == "f2")["criteria"])
        self.assertIn("experience", next(f for f in selected if f["id"] == "f1")["criteria"])
        # Explicit negative evidence remains available to the evaluator.
        self.assertEqual(next(f for f in selected if f["id"] == "f3")["source_excerpt"], "No cuento con licencia C2.")

    def test_weak_initial_matches_expand_coverage_instead_of_implying_absence(self):
        selected = select_evidence_for_vacancy(
            self.facts,
            {"title": "Director de operaciones", "description": "Gestión integral de sedes."},
        )

        self.assertEqual({fact["id"] for fact in selected}, {fact["id"] for fact in self.facts})
        self.assertTrue(all(fact["criteria"] for fact in selected))

    def test_representative_profile_compact_payload_reduces_estimated_tokens_and_keeps_critical_facts(self):
        # Synthetic representative CV; estimate is used only as a local comparison proxy.
        cv_text = ("Experiencia profesional en gestión de proyectos, análisis, coordinación de equipos y reportes. "
                   "Lideré iniciativas de analítica durante 4 años. Profesional en Ingeniería de Sistemas, 2018. "
                   "No cuento con licencia C2. Automaticé reportes financieros con SQL.\n") * 18
        vacancy = {
            "title": "Líder de proyectos de analítica",
            "details": {
                "requirements": ["Profesional en Ingeniería de Sistemas", "Licencia C2 obligatoria", "4 años de experiencia"],
                "responsibilities": ["Liderar proyectos de analítica"],
            },
        }
        selected = select_evidence_for_vacancy(self.facts, vacancy)
        estimate_tokens = lambda value: math.ceil(len(json.dumps(value, ensure_ascii=False)) / 4)
        before = estimate_tokens({"cv": cv_text, "vacancy": vacancy})
        after = estimate_tokens({"profile_evidence": selected, "vacancy": vacancy})

        self.assertLess(after, before)
        self.assertLess(after, before * 0.5)
        selected_ids = {fact["id"] for fact in selected}
        self.assertTrue({"f1", "f2", "f3"}.issubset(selected_ids))


def _docx_bytes(text):
    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def _pdf_bytes(text):
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref}),
    })
    content = DecodedStreamObject()
    pdf_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content.set_data(f"BT /F1 12 Tf 72 720 Td ({pdf_text}) Tj ET".encode("latin-1"))
    page[NameObject("/Contents")] = writer._add_object(content)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


class ProfileEvidenceExtractionTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("evidence-member")
        profile = Profile.objects.create(
            owner=user,
            search_phrases=["Analista de datos"],
            locations=["Medellín"],
            revision_number=1,
        )
        profile.cv_file = "profiles/1/cv/v1.docx"
        profile.save(update_fields=["cv_file"])
        self.revision = ProfileRevision.objects.create(
            profile=profile,
            version=1,
            search_phrases=profile.search_phrases,
            locations=profile.locations,
            cv_file_path=profile.cv_file.name,
        )
        self.config = MatchingConfig.objects.create(
            version=1,
            rubric_version=3,
            prompt_version=6,
            search_prompt="Sugiere cargos relacionados con los hechos del perfil.",
            analysis_prompt="Evalúa la vacante.",
            organization_prompt="Organiza la publicación.",
        )

    def _artifacts_response(self, source_excerpt):
        return ModelCallResult(
            content={
                "facts": [
                    {
                        "category": "skill",
                        "statement": "Automatizó informes con SQL.",
                        "source_excerpt": source_excerpt,
                        "normalized_terms": ["SQL", "informes"],
                        "period": "2022",
                        "metrics": "",
                    },
                    {
                        "category": "experience",
                        "statement": "Teléfono 3001234567.",
                        "source_excerpt": "Celular: 3001234567",
                        "normalized_terms": ["teléfono"],
                        "period": "",
                        "metrics": "",
                    },
                ],
                "keywords": ["Analista de inteligencia de negocio"],
            },
            input_tokens=200,
            output_tokens=50,
        )

    def _extract_from_document(self, suffix, build_document, source_excerpt):
        text = "Experiencia: Automatizó informes con SQL. 2022.\nCorreo: alex@example.test\nCelular: 3001234567"
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            path = f"profiles/test/cv/sample.{suffix}"
            saved_path = ProfileEvidenceExtractionTests._save_file(path, build_document(text))
            self.revision.cv_file_path = saved_path
            self.revision.save(update_fields=["cv_file_path"])
            with patch("matching.evidence.request_model_profile_artifacts", return_value=self._artifacts_response(source_excerpt)) as extract:
                evidence, terms = ensure_profile_artifacts(self.revision, self.config)

        self.assertEqual(len(evidence.facts), 1)
        fact = evidence.facts[0]
        self.assertEqual(fact["source_excerpt"], source_excerpt)
        self.assertNotIn("alex@example.test", str(evidence.facts))
        self.assertNotIn("3001234567", str(evidence.facts))
        self.assertEqual(terms.keywords[0], "Analista de datos")
        self.assertIn("Analista de inteligencia de negocio", terms.keywords)
        self.assertEqual(evidence.input_tokens, 200)
        extract.assert_called_once()

    @staticmethod
    def _save_file(path, content):
        from django.core.files.storage import default_storage
        return default_storage.save(path, ContentFile(content))

    def test_docx_facts_are_source_grounded_and_contact_is_omitted(self):
        self._extract_from_document(
            "docx", _docx_bytes, "Experiencia: Automatizó informes con SQL. 2022.",
        )

    def test_pdf_facts_are_source_grounded_and_contact_is_omitted(self):
        self._extract_from_document(
            "pdf", _pdf_bytes, "Experiencia: Automatizó informes con SQL. 2022.",
        )

    def test_untraceable_model_fact_is_rejected(self):
        with self.assertRaises(InvalidSearchKeywordsError):
            validate_profile_artifacts({
                "facts": [{
                    "category": "skill",
                    "statement": "Maneja SAP.",
                    "source_excerpt": "Experiencia inventada con SAP",
                    "normalized_terms": ["SAP"],
                    "period": "",
                    "metrics": "",
                }],
                "keywords": [],
            }, "Experiencia con SQL")

    @patch("matching.evidence.extract_revision_text", return_value="Experiencia: Automatizó informes con SQL. 2022.")
    @patch("matching.evidence.request_model_profile_artifacts")
    def test_same_revision_and_extractor_reuse_one_extraction(self, extract_artifacts, read_cv):
        extract_artifacts.return_value = self._artifacts_response("Experiencia: Automatizó informes con SQL. 2022.")

        first_evidence, first_terms = ensure_profile_artifacts(self.revision, self.config)
        second_evidence, second_terms = ensure_profile_artifacts(self.revision, self.config)

        self.assertEqual(first_evidence.pk, second_evidence.pk)
        self.assertEqual(first_terms.pk, second_terms.pk)
        self.assertEqual(ProfileEvidence.objects.filter(profile_revision=self.revision).count(), 1)
        self.assertEqual(ProfileSearchTerms.objects.filter(profile_revision=self.revision).count(), 1)
        extract_artifacts.assert_called_once()
        read_cv.assert_called_once_with(self.revision)

    @patch("matching.evidence.extract_revision_text")
    @patch("matching.evidence.request_model_profile_artifacts")
    def test_new_revision_extracts_its_own_cv(self, extract_artifacts, read_cv):
        first_text = "Experiencia: Automatizó informes con SQL. 2022."
        second_text = "Experiencia: Preparó presupuestos con Excel. 2024."
        read_cv.side_effect = [first_text, second_text]
        extract_artifacts.side_effect = [
            self._artifacts_response("Experiencia: Automatizó informes con SQL. 2022."),
            ModelCallResult(content={
                "facts": [{
                    "category": "experience",
                    "statement": "Preparó presupuestos con Excel.",
                    "source_excerpt": "Experiencia: Preparó presupuestos con Excel. 2024.",
                    "normalized_terms": ["presupuestos", "Excel"],
                    "period": "2024",
                    "metrics": "",
                }],
                "keywords": ["Analista financiero"],
            }, input_tokens=180, output_tokens=45),
        ]
        ensure_profile_artifacts(self.revision, self.config)
        self.revision.profile.revision_number = 2
        self.revision.profile.save(update_fields=["revision_number"])
        updated = ProfileRevision.objects.create(
            profile=self.revision.profile,
            version=2,
            search_phrases=["Analista financiero"],
            locations=["Cali"],
            cv_file_path="profiles/1/cv/v2.docx",
        )

        new_evidence, _terms = ensure_profile_artifacts(updated, self.config)

        self.assertEqual(ProfileEvidence.objects.filter(profile_revision=self.revision).count(), 1)
        self.assertEqual(ProfileEvidence.objects.filter(profile_revision=updated).count(), 1)
        self.assertNotEqual(new_evidence.source_sha256, self.revision.evidence_records.get().source_sha256)
        self.assertEqual(new_evidence.facts[0]["source_excerpt"], "Experiencia: Preparó presupuestos con Excel. 2024.")
        self.assertEqual(read_cv.call_count, 2)
        self.assertEqual(extract_artifacts.call_count, 2)

    @patch("matching.evidence.extract_revision_text", return_value="Experiencia de la revisión dos.")
    @patch("matching.evidence.request_model_profile_artifacts", side_effect=OmniRouteError("no disponible"))
    def test_failed_extraction_does_not_fall_back_to_previous_revision(self, extract_artifacts, read_cv):
        ProfileEvidence.objects.create(
            profile_revision=self.revision,
            extractor_version=1,
            source_sha256="a" * 64,
            facts=[{"id": "f1", "category": "skill", "statement": "SQL", "source_excerpt": "SQL"}],
        )
        self.revision.profile.revision_number = 2
        self.revision.profile.save(update_fields=["revision_number"])
        updated = ProfileRevision.objects.create(
            profile=self.revision.profile, version=2, cv_file_path="profiles/1/cv/v2.docx",
        )

        with self.assertRaises(OmniRouteError):
            ensure_profile_artifacts(updated, self.config)

        self.assertFalse(ProfileEvidence.objects.filter(profile_revision=updated).exists())
        self.assertFalse(ProfileSearchTerms.objects.filter(profile_revision=updated).exists())
        extract_artifacts.assert_called_once()
        self.assertEqual(read_cv.call_args.args[0].pk, updated.pk)

    @patch("matching.evidence.extract_revision_text", return_value="Experiencia: Automatizó informes con SQL. 2022.")
    @patch("matching.evidence.request_model_keywords")
    def test_new_search_config_reuses_compact_evidence_without_reading_cv(self, request_keywords, read_cv):
        with patch("matching.evidence.request_model_profile_artifacts", return_value=self._artifacts_response(
            "Experiencia: Automatizó informes con SQL. 2022."
        )):
            evidence, _terms = ensure_profile_artifacts(self.revision, self.config)
        read_cv.reset_mock()
        updated_config = MatchingConfig.objects.create(
            version=2,
            rubric_version=3,
            prompt_version=6,
            search_prompt="Busca roles de análisis y control.",
            analysis_prompt="Evalúa la vacante.",
            organization_prompt="Organiza la publicación.",
            is_active=False,
        )
        request_keywords.return_value = {"keywords": ["Analista de inteligencia de negocio"]}

        _same_evidence, new_terms = ensure_profile_artifacts(self.revision, updated_config)

        self.assertEqual(evidence.pk, _same_evidence.pk)
        self.assertIn("Analista de datos", new_terms.keywords)
        self.assertIn("Analista de inteligencia de negocio", new_terms.keywords)
        read_cv.assert_not_called()
        self.assertEqual(request_keywords.call_args.kwargs["profile_evidence"], evidence.facts)
        self.assertNotIn("profile_text", request_keywords.call_args.kwargs)
