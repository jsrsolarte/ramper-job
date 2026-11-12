from django.contrib.auth import get_user_model
from django.test import TestCase

from jobs.models import Vacancy
from decimal import Decimal

from matching.models import RUBRIC_VERSION, MatchingConfig, VacancyAnalysis
from matching.schemas import (
    InvalidAnalysisError,
    InvalidSearchKeywordsError,
    save_validated_analysis,
    validate_analysis,
    validate_organization,
    validate_search_keywords,
)
from matching.services import RUBRIC_PROMPT
from profiles.models import Profile, ProfileRevision


class AnalysisSchemaTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("member")
        profile = Profile.objects.create(owner=user, revision_number=1)
        revision = ProfileRevision.objects.create(profile=profile, version=1)
        vacancy = Vacancy.objects.create(
            source="elempleo_co",
            title="Analista de datos",
            original_url="https://www.elempleo.com/co/ofertas-trabajo/analista-987",
        )
        config = MatchingConfig.objects.create(
            version=1,
            rubric_version=RUBRIC_VERSION,
            analysis_prompt="Analiza la coincidencia.",
            organization_prompt="Organiza la descripción.",
        )
        self.analysis = VacancyAnalysis.objects.create(
            profile=profile,
            profile_revision=revision,
            vacancy=vacancy,
            matching_config=config,
        )

    def test_valid_response_is_saved_as_completed(self):
        payload = {
            "rubric_version": RUBRIC_VERSION,
            "critical_requirements": [
                {"requirement": "Manejo de SAP", "status": "contradicho", "evidence": "La vacante exige SAP y el CV indica que no lo conoce"}
            ],
            "score_breakdown": {
                "skills": {"score": 4, "status": "cumple", "evidence": "Experiencia"},
                "experience": {"score": 2, "status": "cumple", "evidence": "Procesos"},
                "alignment": {"score": 2, "status": "cumple", "evidence": "Analista"},
                "education": {"score": 1, "status": "cumple", "evidence": "Requisito"},
                "profile_criteria": {"score": 1, "status": "cumple", "evidence": "Perfil"},
            },
            "reasons": ["Experiencia relacionada"],
            "gaps": ["No indica inglés"],
        }

        result = save_validated_analysis(self.analysis, payload)

        self.assertEqual(result.status, VacancyAnalysis.Status.COMPLETED)
        self.assertEqual(result.score, Decimal("8.0"))
        self.assertEqual(result.organization_status, VacancyAnalysis.OrganizationStatus.DEFERRED)
        self.assertEqual(result.score_breakdown["deductions"][0]["points"], 2.0)
        self.assertEqual(result.reasons, ["Experiencia relacionada"])

    def test_invalid_response_stays_pending(self):
        with self.assertRaises(InvalidAnalysisError) as caught:
            save_validated_analysis(self.analysis, {"score": 120, "reasons": [], "gaps": []})

        self.assertEqual(caught.exception.code, "analysis.rubric.version")
        self.assertNotIn("120", caught.exception.code)
        self.assertNotIn("score", caught.exception.code)
        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.PENDING)
        self.assertIsNone(self.analysis.score)

    def test_validation_codes_are_stable_and_do_not_include_response_values(self):
        with self.assertRaises(InvalidAnalysisError) as caught:
            validate_analysis({"rubric_version": RUBRIC_VERSION, "private_sentinel": "profile secret"})

        self.assertEqual(caught.exception.code, "analysis.rubric.criteria_set")
        self.assertNotIn("profile secret", caught.exception.code)
        self.assertNotIn("private_sentinel", caught.exception.code)

        with self.assertRaises(InvalidAnalysisError) as caught:
            validate_analysis({"rubric_version": RUBRIC_VERSION, "score_breakdown": "private response"})
        self.assertEqual(caught.exception.code, "analysis.rubric.criteria_set")
        self.assertNotIn("private response", caught.exception.code)

    def test_decimal_scores_and_critical_requirements_are_validated(self):
        valid = {
            "rubric_version": RUBRIC_VERSION,
            "critical_requirements": [],
            "score_breakdown": {
                "skills": {"score": 4, "status": "cumple", "evidence": "Habilidad"},
                "experience": {"score": 2, "status": "cumple", "evidence": "Experiencia"},
                "alignment": {"score": 2, "status": "cumple", "evidence": "Cargo"},
                "education": {"score": 1, "status": "cumple", "evidence": "Estudios"},
                "profile_criteria": {"score": 1, "status": "cumple", "evidence": "Criterio"},
            },
            "reasons": [],
            "gaps": [],
        }
        self.assertEqual(validate_analysis(valid)["score"], Decimal("10.0"))
        decimal = {**valid, "score_breakdown": {
            **valid["score_breakdown"],
            "skills": {"score": 3.5, "status": "parcial", "evidence": "Experiencia parcial"},
        }}
        self.assertEqual(validate_analysis(decimal)["score"], Decimal("9.5"))
        too_precise = {**decimal, "score_breakdown": {
            **decimal["score_breakdown"],
            "skills": {"score": 3.55, "status": "parcial", "evidence": "Experiencia parcial"},
        }}
        with self.assertRaises(InvalidAnalysisError):
            validate_analysis(too_precise)
        deducted = {**valid, "critical_requirements": [
            {"requirement": "Licencia B1", "status": "contradicho", "evidence": "CV indica que no tiene licencia"},
            {"requirement": "Turnos nocturnos", "status": "contradicho", "evidence": "Vacante exige turnos; perfil indica disponibilidad solo diurna"},
        ]}
        self.assertEqual(validate_analysis(deducted)["score"], Decimal("6.0"))
        below_zero = {**valid, "score_breakdown": {
            "skills": {"score": 1, "status": "parcial", "evidence": "Experiencia básica"},
            "experience": {"score": 0, "status": "sin_evidencia", "evidence": ""},
            "alignment": {"score": 0, "status": "sin_evidencia", "evidence": ""},
            "education": {"score": 0, "status": "sin_evidencia", "evidence": ""},
            "profile_criteria": {"score": 0, "status": "sin_evidencia", "evidence": ""},
        }, "critical_requirements": [
            {"requirement": "Licencia A", "status": "contradicho", "evidence": "CV indica que no la tiene"},
        ]}
        self.assertEqual(validate_analysis(below_zero)["score"], Decimal("0.0"))
        with self.assertRaises(InvalidAnalysisError):
            validate_analysis({
                **valid,
                "score_breakdown": {
                    **valid["score_breakdown"],
                    "skills": {"score": True, "status": "cumple", "evidence": "Habilidad"},
                },
            })
        with self.assertRaises(InvalidAnalysisError):
            validate_analysis({**valid, "gaps": [None]})
        with self.assertRaises(InvalidAnalysisError):
            validate_analysis({key: value for key, value in valid.items() if key != "critical_requirements"})

    def test_missing_critical_evidence_never_deducts_points(self):
        result = validate_analysis({
            "rubric_version": RUBRIC_VERSION,
            "score_breakdown": {
                "skills": {"score": 4, "status": "cumple", "evidence": "Experiencia directa"},
                "experience": {"score": 2, "status": "cumple", "evidence": "Cinco años"},
                "alignment": {"score": 2, "status": "cumple", "evidence": "Sector relevante"},
                "education": {"score": 1, "status": "no_aplica", "evidence": "No hay requisito educativo"},
                "profile_criteria": {"score": 1, "status": "no_aplica", "evidence": "No hay otros criterios"},
            },
            "critical_requirements": [
                {"requirement": "Disponibilidad nocturna", "status": "sin_evidencia", "evidence": ""}
            ],
            "reasons": [], "gaps": [],
        })

        self.assertEqual(result["score"], Decimal("10.0"))
        self.assertEqual(result["deductions"], [])

    def test_critical_requirement_boundaries_and_statuses_match_the_prompt(self):
        base = {
            "rubric_version": RUBRIC_VERSION,
            "critical_requirements": [],
            "score_breakdown": {
                "skills": {"score": 4, "status": "cumple", "evidence": "x"},
                "experience": {"score": 2, "status": "cumple", "evidence": "x"},
                "alignment": {"score": 2, "status": "cumple", "evidence": "x"},
                "education": {"score": 1, "status": "cumple", "evidence": "x"},
                "profile_criteria": {"score": 1, "status": "cumple", "evidence": "x"},
            },
            "reasons": [],
            "gaps": [],
        }
        valid = {**base, "critical_requirements": [
            {"requirement": "r" * 180, "status": "sin_evidencia", "evidence": "e" * 240},
        ]}
        self.assertEqual(len(validate_analysis(valid)["critical_requirements"][0]["requirement"]), 180)

        invalid_requirements = [
            {"requirement": "r" * 181, "status": "cumple", "evidence": "e"},
            {"requirement": "r", "status": "cumple", "evidence": "e" * 241},
            {"requirement": "r", "status": "parcial", "evidence": "e"},
        ]
        for critical_requirement in invalid_requirements:
            with self.subTest(critical_requirement=critical_requirement), self.assertRaises(InvalidAnalysisError):
                validate_analysis({**base, "critical_requirements": [critical_requirement]})

    def test_invalid_critical_requirement_is_not_saved_as_partial_analysis(self):
        payload = {
            "rubric_version": RUBRIC_VERSION,
            "critical_requirements": [
                {"requirement": "r" * 181, "status": "cumple", "evidence": "e"},
            ],
            "score_breakdown": {
                "skills": {"score": 4, "status": "cumple", "evidence": "x"},
                "experience": {"score": 2, "status": "cumple", "evidence": "x"},
                "alignment": {"score": 2, "status": "cumple", "evidence": "x"},
                "education": {"score": 1, "status": "cumple", "evidence": "x"},
                "profile_criteria": {"score": 1, "status": "cumple", "evidence": "x"},
            },
            "reasons": ["No debe persistirse"],
            "gaps": [],
        }

        with self.assertRaises(InvalidAnalysisError) as caught:
            save_validated_analysis(self.analysis, payload)

        self.assertEqual(caught.exception.code, "analysis.rubric.critical_requirement.text_invalid")
        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, VacancyAnalysis.Status.PENDING)
        self.assertIsNone(self.analysis.score)
        self.assertEqual(self.analysis.reasons, [])

    def test_rubric_excludes_personal_attributes_and_distinguishes_missing_evidence(self):
        self.assertIn("discapacidad", RUBRIC_PROMPT)
        self.assertIn("La falta de información no es contradicción", RUBRIC_PROMPT)

    def test_organization_rejects_missing_summary_or_invalid_sections(self):
        for payload in ({"keywords": []}, {"summary": "Resumen", "keywords": [None]}):
            with self.subTest(payload=payload), self.assertRaises(InvalidAnalysisError):
                validate_organization(payload)


class SearchKeywordSchemaTests(TestCase):
    def test_keywords_are_trimmed_deduplicated_and_capped(self):
        result = validate_search_keywords(
            {"keywords": ["  Analista   de procesos ", "analista de procesos", "Mejora continua"]}
        )

        self.assertEqual(result, ["Analista de procesos", "Mejora continua"])

    def test_keywords_reject_invalid_or_empty_entries(self):
        for payload in ({"keywords": [None]}, {"keywords": ["x" * 101]}):
            with self.subTest(payload=payload), self.assertRaises(InvalidSearchKeywordsError):
                validate_search_keywords(payload)

    def test_keywords_reject_more_than_five_distinct_terms(self):
        with self.assertRaises(InvalidSearchKeywordsError):
            validate_search_keywords({"keywords": ["uno", "dos", "tres", "cuatro", "cinco", "seis"]})
