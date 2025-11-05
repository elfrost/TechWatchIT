"""
Tests pour les modèles Pydantic
"""

import pytest
from src.models import (
    ArticleClassification,
    TechnologyType,
    SeverityLevel,
    CategoryType,
    ArticleSummary,
    CriticalAlert
)


class TestArticleClassification:
    """Tests pour ArticleClassification"""

    def test_valid_classification(self):
        """Tester la création d'une classification valide"""
        classification = ArticleClassification(
            technology=TechnologyType.FORTINET,
            category=CategoryType.VULNERABILITY,
            severity_level=SeverityLevel.CRITICAL,
            severity_score=9.5,
            cvss_score=9.8,
            is_security_alert=True,
            impact_analysis="Test impact",
            action_required="Test action",
            cve_references=["CVE-2024-1234"]
        )

        assert classification.technology == TechnologyType.FORTINET
        assert classification.severity_level == SeverityLevel.CRITICAL
        assert classification.severity_score == 9.5
        assert classification.is_security_alert is True
        assert len(classification.cve_references) == 1

    def test_severity_auto_correction(self):
        """Tester l'auto-correction de la sévérité"""
        # Score trop bas pour un CRITICAL
        classification = ArticleClassification(
            technology=TechnologyType.VMWARE,
            category=CategoryType.SECURITY,
            severity_level=SeverityLevel.CRITICAL,
            severity_score=5.0,  # Trop bas!
            is_security_alert=True,
            impact_analysis="Test",
            action_required="Test"
        )

        # Le validator devrait corriger
        assert classification.severity_score >= 8.0

    def test_cve_validation(self):
        """Tester la validation des CVE"""
        classification = ArticleClassification(
            technology=TechnologyType.MICROSOFT,
            category=CategoryType.VULNERABILITY,
            severity_level=SeverityLevel.HIGH,
            severity_score=7.5,
            is_security_alert=True,
            impact_analysis="Test",
            action_required="Test",
            cve_references=[
                "CVE-2024-1234",  # Valide
                "CVE-2023-99999",  # Valide
                "invalid-cve",  # Invalide
                "cve-2024-5678",  # Valide (lowercase ok)
            ]
        )

        # Seuls les CVE valides devraient être conservés
        assert len(classification.cve_references) == 3
        assert all(cve.startswith("CVE-") for cve in classification.cve_references)

    def test_score_boundaries(self):
        """Tester les limites des scores"""
        classification = ArticleClassification(
            technology=TechnologyType.DELL,
            category=CategoryType.UPDATE,
            severity_level=SeverityLevel.LOW,
            severity_score=2.5,  # Dans les limites
            cvss_score=3.0,
            is_security_alert=False,
            impact_analysis="Test",
            action_required="Test"
        )

        assert 1.0 <= classification.severity_score <= 10.0
        assert 0.0 <= classification.cvss_score <= 10.0

    def test_json_serialization(self):
        """Tester la sérialisation JSON"""
        classification = ArticleClassification(
            technology=TechnologyType.SENTINELONE,
            category=CategoryType.PATCH,
            severity_level=SeverityLevel.MEDIUM,
            severity_score=5.0,
            is_security_alert=False,
            impact_analysis="Test impact",
            action_required="Test action"
        )

        # Sérialiser en JSON
        json_data = classification.model_dump_json()
        assert isinstance(json_data, str)
        assert "sentinelone" in json_data

        # Désérialiser
        classification_2 = ArticleClassification.model_validate_json(json_data)
        assert classification_2.technology == classification.technology


class TestArticleSummary:
    """Tests pour ArticleSummary"""

    def test_valid_summary(self):
        """Tester la création d'un résumé valide"""
        summary = ArticleSummary(
            summary="Test summary" * 20,  # Assez long
            key_points=["Point 1", "Point 2", "Point 3"],
            business_impact="Impact test",
            technical_details="Details test",
            similar_incidents=["Incident 1"],
            recommendations=["Action 1", "Action 2"]
        )

        assert len(summary.key_points) >= 3
        assert len(summary.summary) <= 500

    def test_key_points_validation(self):
        """Tester la validation des points clés"""
        summary = ArticleSummary(
            summary="Test",
            key_points=["Point 1", "", "Point 2", "  ", "Point 3"],  # Avec espaces vides
            business_impact="Impact",
            technical_details="Details"
        )

        # Les points vides devraient être filtrés
        assert all(point.strip() for point in summary.key_points)

    def test_min_key_points(self):
        """Tester le minimum de points clés"""
        with pytest.raises(ValueError):
            # Moins de 3 points devrait échouer
            ArticleSummary(
                summary="Test",
                key_points=["Point 1", "Point 2"],  # Seulement 2
                business_impact="Impact",
                technical_details="Details"
            )


class TestCriticalAlert:
    """Tests pour CriticalAlert"""

    def test_complete_alert(self):
        """Tester la création d'une alerte complète"""
        classification = ArticleClassification(
            technology=TechnologyType.FORTINET,
            category=CategoryType.VULNERABILITY,
            severity_level=SeverityLevel.CRITICAL,
            severity_score=9.5,
            is_security_alert=True,
            impact_analysis="Critical impact",
            action_required="Immediate action"
        )

        summary = ArticleSummary(
            summary="Critical vulnerability",
            key_points=["Point 1", "Point 2", "Point 3"],
            business_impact="High",
            technical_details="Technical info"
        )

        alert = CriticalAlert(
            article_id=123,
            title="Critical Security Alert",
            classification=classification,
            summary=summary,
            urgency_level="immediate",
            affected_systems=["FortiGate", "FortiOS"],
            rag_context="Additional context from RAG"
        )

        assert alert.article_id == 123
        assert alert.urgency_level == "immediate"
        assert len(alert.affected_systems) == 2
        assert alert.classification.severity_level == SeverityLevel.CRITICAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
